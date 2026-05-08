// Copyright 2024 Neshama. All Rights Reserved.
// Neshama SDK - License Manager Header
// Handles license validation, offline grace period, region isolation, and feature gating for UE5

#pragma once

#include "CoreMinimal.h"
#include "NeshamaConfig.h"
#include "LicenseManager.generated.h"

// ============================================================================
// Delegates（非动态，用于C++内部回调，支持BindLambda）
// ============================================================================

/** Callback when license validation completes */
DECLARE_DELEGATE_TwoParams(FNeshamaLicenseValidated, bool, const FString&);

/** Callback when license activation completes */
DECLARE_DELEGATE_TwoParams(FNeshamaLicenseActivated, bool, const FString&);

// ============================================================================
// FLicenseInfo - License information structure
// ============================================================================

/**
 * License information returned from the validation server.
 * Mirrors the server-side LicenseValidationResult.
 * Includes region fields for cross-region arbitrage prevention.
 */
USTRUCT(BlueprintType)
struct NESHAMASDK_API FLicenseInfo
{
    GENERATED_BODY()

    /** Whether the license is valid */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    bool bValid = false;

    /** Current plan: free, indie, studio, enterprise */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    FString Plan = TEXT("free");

    /** Maximum number of NPCs allowed */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    int32 MaxNpcs = 3;

    /** Available features for this plan */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    TArray<FString> Features;

    /** License expiration time (ISO 8601) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    FString ExpiresAt;

    /** License region: "cn" or "global" */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    FString Region = TEXT("global");

    /** Whether the license region matches the request region */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    bool bRegionMatch = true;

    /** Grace period deadline (ISO 8601), empty if not in grace */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    FString GraceUntil;

    /** Last successful validation time (ISO 8601) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    FString LastValidatedAt;

    /** Error message if validation/activation failed */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neshama|License")
    FString Error;

    /**
     * Check if a specific feature is available.
     * @param FeatureName Feature identifier to check
     * @return True if the feature is available in this license
     */
    bool HasFeature(const FString& FeatureName) const
    {
        return Features.Contains(FeatureName);
    }

    /**
     * Get a human-readable region mismatch error message.
     * Returns empty string if regions match.
     */
    FString GetRegionMismatchMessage() const
    {
        if (bRegionMatch) return TEXT("");
        FString RegionName = (Region == TEXT("cn")) ? TEXT("China (中国区)") : TEXT("Global (国际区)");
        return FString::Printf(TEXT("License key region mismatch. This key is for %s. Cross-region usage is not permitted."), *RegionName);
    }
};

// ============================================================================
// ULicenseManager - License management subsystem
// ============================================================================

/**
 * License Manager — handles license validation, offline grace period,
 * region isolation, and feature gating for the Neshama SDK in Unreal Engine 5.
 *
 * Region Isolation:
 *   The SDK automatically detects its region from the configured API URL:
 *   - api.neshama.cn  → China region (cn)
 *   - api.neshama.pw  → Global region (global)
 *   License keys with mismatched regions are rejected with a clear error.
 *
 * Usage:
 *   ULicenseManager* LM = ULicenseManager::Get();
 *   LM->ValidateLicenseWithCallback(Key, MachineId, FNeshamaLicenseValidated::CreateLambda(...));
 *   if (LM->HasFeature("social_engine")) { ... }
 *   int32 MaxNPCs = LM->GetMaxNPCs();
 */
UCLASS(BlueprintType, Blueprintable)
class NESHAMASDK_API ULicenseManager : public UObject
{
    GENERATED_BODY()

public:
    // ========================================================================
    // Construction
    // ========================================================================

    ULicenseManager();
    virtual ~ULicenseManager();

    /**
     * Get the singleton license manager instance.
     * Creates one if it doesn't exist.
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License", meta = (DisplayName = "Get License Manager"))
    static ULicenseManager* Get();

    // ========================================================================
    // License Validation
    // ========================================================================

    /**
     * Validate a license key with the server.
     * On success, caches the result for offline grace period.
     * The server detects the request region from the Host header.
     *
     * @param LicenseKey The license key to validate
     * @param MachineId Hardware fingerprint of this machine
     * @param OnComplete Callback when validation completes
     */
    UFUNCTION(BlueprintCallable, Category = "Neshama|License",
        meta = (DisplayName = "Validate License",
                ToolTip = "Validate a license key with the Neshama server"))
    void ValidateLicense(const FString& LicenseKey, const FString& MachineId);

    /** Validate license (C++ callback version) */
    void ValidateLicenseWithCallback(const FString& LicenseKey, const FString& MachineId, const FNeshamaLicenseValidated& OnComplete);

    /**
     * Initialize the license manager on startup.
     * If online, validates the stored license; if offline, uses cached license + grace period.
     *
     * @param OnComplete Callback when initialization completes
     */
    UFUNCTION(BlueprintCallable, Category = "Neshama|License",
        meta = (DisplayName = "Initialize License",
                ToolTip = "Initialize license manager (auto-validates stored key)"))
    void InitializeLicense();

    /** Initialize license (C++ callback version) */
    void InitializeLicenseWithCallback(const FNeshamaLicenseValidated& OnComplete);

    /**
     * Activate (bind) a license key to this machine.
     * Call this once after the user enters their license key.
     * The server checks that the license region matches the API region.
     *
     * @param LicenseKey The license key to activate
     * @param MachineId Hardware fingerprint of this machine
     * @param OnComplete Callback when activation completes
     */
    UFUNCTION(BlueprintCallable, Category = "Neshama|License",
        meta = (DisplayName = "Activate License",
                ToolTip = "Activate a license key and bind it to this machine"))
    void ActivateLicense(const FString& LicenseKey, const FString& MachineId);

    /** Activate license (C++ callback version) */
    void ActivateLicenseWithCallback(const FString& LicenseKey, const FString& MachineId, const FNeshamaLicenseActivated& OnComplete);

    /**
     * Deactivate (unbind) this machine from the current license.
     *
     * @param OnComplete Callback when deactivation completes
     */
    UFUNCTION(BlueprintCallable, Category = "Neshama|License",
        meta = (DisplayName = "Deactivate License",
                ToolTip = "Deactivate the current license on this machine"))
    void DeactivateLicense();

    /** Deactivate license (C++ callback version) */
    void DeactivateLicenseWithCallback(const FNeshamaLicenseActivated& OnComplete);

    // ========================================================================
    // Feature & Plan Queries
    // ========================================================================

    /**
     * Check if a feature is available in the current license.
     * @param FeatureName Feature identifier (e.g., "social_engine", "l2_memory")
     * @return True if the feature is available
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Has Feature",
                ToolTip = "Check if a feature is available in the current license"))
    bool HasFeature(const FString& FeatureName) const;

    /**
     * Get the maximum number of NPCs allowed by the current license.
     * @return Max NPC count (3 for free, -1 for unlimited)
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Get Max NPCs",
                ToolTip = "Get the maximum number of NPCs allowed"))
    int32 GetMaxNPCs() const;

    /**
     * Get the current plan name.
     * @return Plan name ("free", "indie", "studio", "enterprise")
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Get Current Plan",
                ToolTip = "Get the current license plan name"))
    FString GetCurrentPlan() const;

    /**
     * Get the current license info.
     * @return Current license information
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Get License Info",
                ToolTip = "Get the current license information"))
    FLicenseInfo GetLicenseInfo() const;

    /**
     * Check if the license manager has been initialized.
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License")
    bool IsInitialized() const { return bInitialized; }

    /**
     * Get the detected region based on the configured server URL.
     * @return "cn" or "global"
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Get Detected Region",
                ToolTip = "Get the region detected from the server URL"))
    FString GetDetectedRegion() const;

    /**
     * Get a display-friendly region name.
     * @param RegionCode Region code ("cn" or "global")
     * @return Display name like "China (中国区)" or "Global (国际区)"
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Get Region Display Name"))
    static FString GetRegionDisplayName(const FString& RegionCode);

    // ========================================================================
    // Machine ID
    // ========================================================================

    /**
     * Get the machine fingerprint for this device.
     * Combines CPU ID + GPU ID + MAC address → SHA256
     * @return Machine fingerprint string
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License",
        meta = (DisplayName = "Get Machine ID",
                ToolTip = "Get the hardware fingerprint for this machine"))
    static FString GetMachineId();

    // ========================================================================
    // License Key Storage
    // ========================================================================

    /**
     * Store a license key (persisted in game save).
     */
    UFUNCTION(BlueprintCallable, Category = "Neshama|License")
    void StoreLicenseKey(const FString& Key);

    /**
     * Get the stored license key.
     */
    UFUNCTION(BlueprintPure, Category = "Neshama|License")
    FString GetStoredLicenseKey() const;

    /**
     * Clear the stored license key and cache.
     */
    UFUNCTION(BlueprintCallable, Category = "Neshama|License")
    void ClearStoredLicense();

private:
    // Current license info
    UPROPERTY()
    FLicenseInfo CurrentLicense;

    // Whether the manager has been initialized
    bool bInitialized = false;

    // Cached machine ID
    FString CachedMachineId;

    // Detected region from server URL
    mutable FString DetectedRegionCode;

    // Singleton instance
    static ULicenseManager* SingletonInstance;

    // ── Internal Methods ───────────────────────────────────────────────────

    /** Detect region from the configured server URL */
    FString DetectRegion() const;

    /** Make HTTP POST request to the license server */
    void MakeLicenseRequest(
        const FString& Endpoint,
        const TSharedRef<FJsonObject>& RequestBody,
        TFunction<void(bool, const TSharedPtr<FJsonObject>&)> OnResponse
    );

    /** Parse license info from JSON response */
    FLicenseInfo ParseLicenseInfo(const TSharedPtr<FJsonObject>& JsonObj) const;

    /** Create a free-tier license */
    FLicenseInfo CreateFreeLicense() const;

    /** Get offline license from cache with grace period */
    FLicenseInfo GetOfflineLicense() const;

    /** Save license info to local cache */
    void CacheLicenseLocally(const FLicenseInfo& Info);

    /** Load cached license info */
    bool LoadCachedLicense(FLicenseInfo& OutInfo) const;

    /** Simple XOR encrypt/decrypt for local storage */
    FString SimpleEncrypt(const FString& PlainText) const;
    FString SimpleDecrypt(const FString& CipherText) const;

    /** Compute SHA256 hash */
    static FString ComputeSHA256(const FString& Input);

    /** Get MAC address / device ID */
    static FString GetMacAddress();
};
