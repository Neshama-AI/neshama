// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - License Manager Implementation
// Handles license validation, offline grace period, region isolation, and feature gating

#include "LicenseManager.h"
#include "NeshamaClient.h"
#include "Misc/SecureHash.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "HAL/PlatformProcess.h"
#include "Misc/Base64.h"
#include "Misc/ConfigCacheIni.h"

// ============================================================================
// Static Instance
// ============================================================================

ULicenseManager* ULicenseManager::SingletonInstance = nullptr;

// ============================================================================
// Construction
// ============================================================================

ULicenseManager::ULicenseManager()
{
    DetectedRegionCode = DetectRegion();
}

ULicenseManager::~ULicenseManager()
{
    if (SingletonInstance == this)
    {
        SingletonInstance = nullptr;
    }
}

ULicenseManager* ULicenseManager::Get()
{
    if (!SingletonInstance)
    {
        // Create a persistent instance via NewObject with transient package
        SingletonInstance = NewObject<ULicenseManager>(
            GetTransientPackage(),
            ULicenseManager::StaticClass(),
            NAME_None,
            RF_MarkAsRootSet
        );
    }
    return SingletonInstance;
}

// ============================================================================
// Region Detection
// ============================================================================

FString ULicenseManager::DetectRegion() const
{
    // Read the server URL from NeshamaConfig
    UNeshamaConfig* Config = NewObject<UNeshamaConfig>();
    FString ServerUrl = Config->ServerUrl;

    if (ServerUrl.Contains(TEXT("neshama.cn")))
    {
        return TEXT("cn");
    }
    return TEXT("global");
}

FString ULicenseManager::GetDetectedRegion() const
{
    if (DetectedRegionCode.IsEmpty())
    {
        DetectedRegionCode = DetectRegion();
    }
    return DetectedRegionCode;
}

FString ULicenseManager::GetRegionDisplayName(const FString& RegionCode)
{
    if (RegionCode == TEXT("cn"))
    {
        return TEXT("China (中国区)");
    }
    return TEXT("Global (国际区)");
}

// ============================================================================
// Machine ID
// ============================================================================

FString ULicenseManager::GetMachineId()
{
    FString CpuId = FPlatformMisc::GetCPUBrand();
    FString GpuId; // FPlatformMisc doesn't expose GPU name directly in all platforms
    FString MacAddr = GetMacAddress();

    FString Raw = FString::Printf(TEXT("%s|%s|%s"), *CpuId, *GpuId, *MacAddr);
    return ComputeSHA256(Raw);
}

FString ULicenseManager::GetMacAddress()
{
    // Use a stable device identifier
    // On most platforms this maps to a hardware ID
    return FPlatformMisc::GetDeviceId();
}

FString ULicenseManager::ComputeSHA256(const FString& Input)
{
    FTCHARToUTF8 UTF8Str(*Input);
    FSHA1 Hash;
    Hash.Update(reinterpret_cast<const uint8*>(UTF8Str.Get()), UTF8Str.Length());
    Hash.Final();
    
    FString Result;
    const uint8* Bytes = Hash.m_digest;
    for (int32 i = 0; i < 20; ++i)
    {
        Result += FString::Printf(TEXT("%02x"), Bytes[i]);
    }
    return Result;
}

// ============================================================================
// License Validation
// ============================================================================

void ULicenseManager::ValidateLicenseWithCallback(
    const FString& LicenseKey,
    const FString& MachineId,
    const FNeshamaLicenseValidated& OnComplete)
{
    TSharedPtr<FJsonObject> RequestBody = MakeShareable(new FJsonObject());
    RequestBody->SetStringField(TEXT("license_key"), LicenseKey);
    RequestBody->SetStringField(TEXT("machine_id"), MachineId);

    MakeLicenseRequest(TEXT("/api/license/validate"), RequestBody,
        [this, OnComplete](bool bSuccess, const TSharedPtr<FJsonObject>& Response)
        {
            if (bSuccess && Response.IsValid())
            {
                CurrentLicense = ParseLicenseInfo(Response);
                CacheLicenseLocally(CurrentLicense);

                if (!CurrentLicense.bRegionMatch)
                {
                    FString Msg = CurrentLicense.GetRegionMismatchMessage();
                    UE_LOG(LogTemp, Error, TEXT("[NeshamaLicense] REGION MISMATCH: %s"), *Msg);
                    OnComplete.ExecuteIfBound(false, Msg);
                }
                else if (CurrentLicense.bValid)
                {
                    UE_LOG(LogTemp, Log, TEXT("[NeshamaLicense] Validated: plan=%s, region=%s, max_npcs=%d"),
                        *CurrentLicense.Plan, *CurrentLicense.Region, CurrentLicense.MaxNpcs);
                    OnComplete.ExecuteIfBound(true, TEXT(""));
                }
                else
                {
                    OnComplete.ExecuteIfBound(false, CurrentLicense.Error);
                }
            }
            else
            {
                OnComplete.ExecuteIfBound(false, TEXT("License validation request failed"));
            }
        }
    );
}


void ULicenseManager::InitializeLicenseWithCallback(const FNeshamaLicenseValidated& OnComplete)
{
    FString StoredKey = GetStoredLicenseKey();
    if (StoredKey.IsEmpty())
    {
        UE_LOG(LogTemp, Log, TEXT("[NeshamaLicense] No stored license, using Free tier"));
        CurrentLicense = CreateFreeLicense();
        bInitialized = true;
        OnComplete.ExecuteIfBound(true, TEXT(""));
        return;
    }

    FString MachineId = GetMachineId();
    ValidateLicenseWithCallback(StoredKey, MachineId, FNeshamaLicenseValidated::CreateLambda(
        [this, OnComplete](bool bSuccess, const FString& Error)
        {
            bInitialized = true;
            if (!bSuccess)
            {
                UE_LOG(LogTemp, Warning, TEXT("[NeshamaLicense] Online validation failed, checking offline: %s"), *Error);
                CurrentLicense = GetOfflineLicense();
            }
            OnComplete.ExecuteIfBound(bSuccess, Error);
        }
    ));
}

void ULicenseManager::ActivateLicenseWithCallback(
    const FString& LicenseKey,
    const FString& MachineId,
    const FNeshamaLicenseActivated& OnComplete)
{
    TSharedPtr<FJsonObject> RequestBody = MakeShareable(new FJsonObject());
    RequestBody->SetStringField(TEXT("license_key"), LicenseKey);
    RequestBody->SetStringField(TEXT("machine_id"), MachineId);

    MakeLicenseRequest(TEXT("/api/license/activate"), RequestBody,
        [this, LicenseKey, OnComplete](bool bSuccess, const TSharedPtr<FJsonObject>& Response)
        {
            if (bSuccess && Response.IsValid())
            {
                bool bSuccessResult = Response->GetBoolField(TEXT("success"));
                FString Message = Response->GetStringField(TEXT("message"));

                if (bSuccessResult)
                {
                    StoreLicenseKey(LicenseKey);
                    UE_LOG(LogTemp, Log, TEXT("[NeshamaLicense] License activated successfully"));
                }
                else if (Message.Contains(TEXT("region mismatch")))
                {
                    UE_LOG(LogTemp, Error, TEXT("[NeshamaLicense] REGION MISMATCH: %s"), *Message);
                }

                OnComplete.ExecuteIfBound(bSuccessResult, Message);
            }
            else
            {
                OnComplete.ExecuteIfBound(false, TEXT("Activation request failed"));
            }
        }
    );
}

void ULicenseManager::DeactivateLicenseWithCallback(const FNeshamaLicenseActivated& OnComplete)
{
    FString StoredKey = GetStoredLicenseKey();
    if (StoredKey.IsEmpty())
    {
        OnComplete.ExecuteIfBound(false, TEXT("No stored license to deactivate"));
        return;
    }

    FString MachineId = GetMachineId();
    TSharedPtr<FJsonObject> RequestBody = MakeShareable(new FJsonObject());
    RequestBody->SetStringField(TEXT("license_key"), StoredKey);
    RequestBody->SetStringField(TEXT("machine_id"), MachineId);

    MakeLicenseRequest(TEXT("/api/license/deactivate"), RequestBody,
        [this, OnComplete](bool bSuccess, const TSharedPtr<FJsonObject>& Response)
        {
            if (bSuccess && Response.IsValid())
            {
                bool bSuccessResult = Response->GetBoolField(TEXT("success"));
                if (bSuccessResult)
                {
                    ClearStoredLicense();
                    CurrentLicense = CreateFreeLicense();
                    UE_LOG(LogTemp, Log, TEXT("[NeshamaLicense] License deactivated"));
                }
                FString Message = Response->GetStringField(TEXT("message"));
                OnComplete.ExecuteIfBound(bSuccessResult, Message);
            }
            else
            {
                OnComplete.ExecuteIfBound(false, TEXT("Deactivation request failed"));
            }
        }
    );
}

// ============================================================================
// Feature & Plan Queries
// ============================================================================

bool ULicenseManager::HasFeature(const FString& FeatureName) const
{
    if (!bInitialized)
    {
        UE_LOG(LogTemp, Warning, TEXT("[NeshamaLicense] Not initialized, call InitializeLicense first"));
        return false;
    }
    return CurrentLicense.HasFeature(FeatureName);
}

int32 ULicenseManager::GetMaxNPCs() const
{
    if (!bInitialized) return 3;
    return CurrentLicense.MaxNpcs;
}

FString ULicenseManager::GetCurrentPlan() const
{
    if (!bInitialized) return TEXT("free");
    return CurrentLicense.Plan;
}

FLicenseInfo ULicenseManager::GetLicenseInfo() const
{
    return CurrentLicense;
}

// ============================================================================
// License Key Storage
// ============================================================================

void ULicenseManager::StoreLicenseKey(const FString& Key)
{
    FString Encrypted = SimpleEncrypt(Key);
    GConfig->SetString(TEXT("NeshamaLicense"), TEXT("Key"), *Encrypted, GGameUserSettingsIni);
    GConfig->Flush(false, GGameUserSettingsIni);
}

FString ULicenseManager::GetStoredLicenseKey() const
{
    FString Encrypted;
    if (GConfig->GetString(TEXT("NeshamaLicense"), TEXT("Key"), Encrypted, GGameUserSettingsIni))
    {
        return SimpleDecrypt(Encrypted);
    }
    return TEXT("");
}

void ULicenseManager::ClearStoredLicense()
{
    GConfig->EmptySection(TEXT("NeshamaLicense"), GGameUserSettingsIni);
    GConfig->Flush(false, GGameUserSettingsIni);
}

// ============================================================================
// HTTP Request Helper
// ============================================================================

void ULicenseManager::MakeLicenseRequest(
    const FString& Endpoint,
    const TSharedPtr<FJsonObject>& RequestBody,
    TFunction<void(bool, const TSharedPtr<FJsonObject>&)> OnResponse)
{
    if (!RequestBody.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[NeshamaLicense] MakeLicenseRequest called with null RequestBody"));
        OnResponse(false, nullptr);
        return;
    }

    UNeshamaConfig* Config = NewObject<UNeshamaConfig>();
    FString BaseUrl = Config->ServerUrl;
    FString Url = BaseUrl + Endpoint;

    // Serialize request body
    FString JsonStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonStr);
    FJsonSerializer::Serialize(RequestBody, Writer);

    // Create HTTP request
    TSharedRef<IHttpRequest> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(Url);
    HttpRequest->SetVerb(TEXT("POST"));
    HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    HttpRequest->SetContentAsString(JsonStr);
    HttpRequest->SetTimeout(10.0f);

    HttpRequest->OnProcessRequestComplete().BindLambda(
        [OnResponse](FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
        {
            if (!bWasSuccessful || !Response.IsValid())
            {
                OnResponse(false, nullptr);
                return;
            }

            int32 StatusCode = Response->GetResponseCode();
            if (StatusCode != 200)
            {
                OnResponse(false, nullptr);
                return;
            }

            FString ResponseStr = Response->GetContentAsString();
            TSharedPtr<FJsonObject> JsonObject;
            TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseStr);

            if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
            {
                OnResponse(true, JsonObject);
            }
            else
            {
                OnResponse(false, nullptr);
            }
        }
    );

    HttpRequest->ProcessRequest();
}

// ============================================================================
// JSON Parsing
// ============================================================================

FLicenseInfo ULicenseManager::ParseLicenseInfo(const TSharedPtr<FJsonObject>& JsonObj) const
{
    FLicenseInfo Info;

    if (!JsonObj.IsValid()) return Info;

    Info.bValid = JsonObj->GetBoolField(TEXT("valid"));
    Info.Plan = JsonObj->GetStringField(TEXT("plan"));
    Info.MaxNpcs = JsonObj->GetIntegerField(TEXT("max_npcs"));
    Info.ExpiresAt = JsonObj->GetStringField(TEXT("expires_at"));
    Info.Region = JsonObj->GetStringField(TEXT("region"));
    Info.bRegionMatch = JsonObj->GetBoolField(TEXT("region_match"));

    // Optional fields
    if (JsonObj->HasField(TEXT("grace_until")))
    {
        Info.GraceUntil = JsonObj->GetStringField(TEXT("grace_until"));
    }
    if (JsonObj->HasField(TEXT("last_validated_at")))
    {
        Info.LastValidatedAt = JsonObj->GetStringField(TEXT("last_validated_at"));
    }
    if (JsonObj->HasField(TEXT("error")))
    {
        Info.Error = JsonObj->GetStringField(TEXT("error"));
    }

    // Features array
    const TArray<TSharedPtr<FJsonValue>>* FeaturesArray;
    if (JsonObj->TryGetArrayField(TEXT("features"), FeaturesArray))
    {
        for (const auto& Feature : *FeaturesArray)
        {
            Info.Features.Add(Feature->AsString());
        }
    }

    return Info;
}

FLicenseInfo ULicenseManager::CreateFreeLicense() const
{
    FLicenseInfo Info;
    Info.bValid = false;
    Info.Plan = TEXT("free");
    Info.MaxNpcs = 3;
    Info.Features = { TEXT("basic_emotion"), TEXT("ocean_personality"), TEXT("l0_memory") };
    Info.ExpiresAt = TEXT("");
    Info.Region = GetDetectedRegion();
    Info.bRegionMatch = true;
    Info.GraceUntil = TEXT("");
    Info.LastValidatedAt = FDateTime::UtcNow().ToIso8601();
    return Info;
}

FLicenseInfo ULicenseManager::GetOfflineLicense() const
{
    FLicenseInfo Cached;
    if (LoadCachedLicense(Cached))
    {
        // TODO: Check grace period against cached last_validated_at
        return Cached;
    }
    return CreateFreeLicense();
}

void ULicenseManager::CacheLicenseLocally(const FLicenseInfo& Info)
{
    // Serialize to JSON and store encrypted
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetBoolField(TEXT("valid"), Info.bValid);
    JsonObject->SetStringField(TEXT("plan"), Info.Plan);
    JsonObject->SetNumberField(TEXT("max_npcs"), Info.MaxNpcs);
    JsonObject->SetStringField(TEXT("expires_at"), Info.ExpiresAt);
    JsonObject->SetStringField(TEXT("region"), Info.Region);
    JsonObject->SetBoolField(TEXT("region_match"), Info.bRegionMatch);
    JsonObject->SetStringField(TEXT("grace_until"), Info.GraceUntil);
    JsonObject->SetStringField(TEXT("last_validated_at"), FDateTime::UtcNow().ToIso8601());

    FString JsonStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonStr);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    FString Encrypted = SimpleEncrypt(JsonStr);
    GConfig->SetString(TEXT("NeshamaLicense"), TEXT("Cache"), *Encrypted, GGameUserSettingsIni);
    GConfig->SetString(TEXT("NeshamaLicense"), TEXT("ValidatedAt"), *FDateTime::UtcNow().ToIso8601(), GGameUserSettingsIni);
    GConfig->Flush(false, GGameUserSettingsIni);
}

bool ULicenseManager::LoadCachedLicense(FLicenseInfo& OutInfo) const
{
    FString Encrypted;
    if (!GConfig->GetString(TEXT("NeshamaLicense"), TEXT("Cache"), Encrypted, GGameUserSettingsIni))
    {
        return false;
    }

    FString JsonStr = SimpleDecrypt(Encrypted);
    if (JsonStr.IsEmpty()) return false;

    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);

    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
    {
        OutInfo = ParseLicenseInfo(JsonObject);
        return true;
    }

    return false;
}

// ============================================================================
// Encryption
// ============================================================================

FString ULicenseManager::SimpleEncrypt(const FString& PlainText) const
{
    // XOR with key, then Base64 encode
    const FString Key = TEXT("nsh_enc_key_2024");
    FTCHARToUTF8 KeyUtf8(*Key);
    FTCHARToUTF8 PlainUtf8(*PlainText);

    TArray<uint8> Result;
    Result.SetNumUninitialized(PlainUtf8.Length());

    for (int32 i = 0; i < PlainUtf8.Length(); i++)
    {
        Result[i] = PlainUtf8.Get()[i] ^ KeyUtf8.Get()[i % KeyUtf8.Length()];
    }

    return FBase64::Encode(Result);
}

FString ULicenseManager::SimpleDecrypt(const FString& CipherText) const
{
    // Base64 decode, then XOR with key
    const FString Key = TEXT("nsh_enc_key_2024");
    FTCHARToUTF8 KeyUtf8(*Key);

    TArray<uint8> Decoded;
    if (!FBase64::Decode(CipherText, Decoded))
    {
        return TEXT("");
    }

    TArray<uint8> Result;
    Result.SetNumUninitialized(Decoded.Num());

    for (int32 i = 0; i < Decoded.Num(); i++)
    {
        Result[i] = Decoded[i] ^ KeyUtf8.Get()[i % KeyUtf8.Length()];
    }

    return FString(UTF8_TO_TCHAR(Result.GetData()));
}


// ============================================================================
// Blueprint友好的无回调方法实现
// ============================================================================

void ULicenseManager::ValidateLicense(const FString& LicenseKey, const FString& MachineId)
{
    FNeshamaLicenseValidated DummyCallback;
    ValidateLicenseWithCallback(LicenseKey, MachineId, DummyCallback);
}

void ULicenseManager::InitializeLicense()
{
    FNeshamaLicenseValidated DummyCallback;
    InitializeLicenseWithCallback(DummyCallback);
}

void ULicenseManager::ActivateLicense(const FString& LicenseKey, const FString& MachineId)
{
    FNeshamaLicenseActivated DummyCallback;
    ActivateLicenseWithCallback(LicenseKey, MachineId, DummyCallback);
}

void ULicenseManager::DeactivateLicense()
{
    FNeshamaLicenseActivated DummyCallback;
    DeactivateLicenseWithCallback(DummyCallback);
}

