# Neshama AI 邮件域名配置指南

> 本文档为 JOJO 提供，用于配置 cloud.neshama.ai 的邮件发送域名验证（SPF、DKIM、DMARC）。

## 📋 概述

为确保从 @neshama.ai 发送的邮件能够成功送达并避免被标记为垃圾邮件，需要配置以下三项 DNS 记录：

| 记录类型 | 用途 | 优先级 |
|---------|------|--------|
| **SPF** | 授权服务器发送邮件 | 必须 |
| **DKIM** | 邮件签名验证 | 必须 |
| **DMARC** | 域名保护策略 | 推荐 |

---

## �Step 1: 确定邮件发送服务提供商

Neshama AI 使用第三方邮件发送服务。以下是常见选项：

### 推荐方案
- **SendGrid** - 功能完善，免费额度充足
- **Amazon SES** - 成本低，适合大量邮件
- **Mailgun** - 开发者友好

### 获取验证信息
在邮件服务提供商处，您会获得：
- **发送域名**（如 `neshama.ai`）
- **SPF 记录值**（如 `v=spf1 include:sendgrid.net ~all`）
- **DKIM 记录**（域名和公钥值）

---

## �Step 2: 配置 SPF 记录

### 什么是 SPF？
SPF（Sender Policy Framework）告诉收件服务器哪些服务器被授权代表您的域名发送邮件。

### 添加步骤

1. **登录您的 DNS 管理控制台**
   - 您的域名注册商（如 GoDaddy、Namecheap、阿里云）或 DNS 服务商（如 Cloudflare）

2. **添加 TXT 记录**
   ```
   记录类型: TXT
   主机名/名称: @ (或留空)
   值/内容: v=spf1 include:spf.sendgrid.net ~all
   TTL: 3600 (或自动)
   ```

3. **如果使用多个发送服务，合并 SPF**
   ```
   v=spf1 include:spf.sendgrid.net include:amazonses.com ~all
   ```

### ⚠️ 注意事项
- 每个域名只能有 **一个** SPF TXT 记录
- 如果已有 SPF 记录，请将新的 include 语句添加到现有记录中
- `~all` 表示软失败（建议），`-all` 表示硬失败（严格）

---

## �Step 3: 配置 DKIM 签名

### 什么是 DKIM？
DKIM（DomainKeys Identified Mail）使用公钥加密技术为邮件添加数字签名，收件服务器可验证邮件确实来自声称的域名。

### 添加步骤

1. **从邮件服务商获取 DKIM 记录**
   - 发送服务商通常会提供类似以下信息：
   ```
   域名: selector._domainkey.neshama.ai
   类型: TXT
   值: v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA...
   ```

2. **在 DNS 中添加 DKIM 记录**
   ```
   记录类型: TXT
   主机名/名称: selector._domainkey.neshama.ai
                (注意：selector 是您服务商提供的标识符)
   值/内容: v=DKIM1; k=rsa; p=您的公钥...
   TTL: 3600 (或自动)
   ```

3. **验证 DKIM 配置**
   - 大多数邮件服务商提供 DKIM 验证工具
   - 可能需要 24-48 小时让 DNS 记录完全传播

---

## �Step 4: 配置 DMARC 策略

### 什么是 DMARC？
DMARC（Domain-based Message Authentication, Reporting & Conformance）基于 SPF 和 DKIM，提供域名保护并接收邮件验证报告。

### DMARC 策略级别

| 策略 | 说明 |
|-----|------|
| `p=none` | 仅监控，不采取行动 |
| `p=quarantine` | 将可疑邮件标记为垃圾邮件 |
| `p=reject` | 完全拒绝可疑邮件（最严格） |

### 推荐初始配置（监控模式）

1. **添加 DMARC TXT 记录**
   ```
   记录类型: TXT
   主机名/名称: _dmarc.neshama.ai
   值/内容: v=DMARC1; p=none; rua=mailto:dmarc-reports@neshama.ai; ruf=mailto:dmarc-reports@neshama.ai
   TTL: 3600 (或自动)
   ```

### 字段说明

| 字段 | 说明 |
|-----|------|
| `v=DMARC1` | DMARC 版本（固定值） |
| `p=none` | 策略：无行动，仅监控 |
| `rua=mailto:` | 聚合报告发送地址 |
| `ruf=mailto:` | 故障报告发送地址 |

### 逐步加强策略（可选）

在确认邮件发送正常后，逐步升级：

```
# 阶段1：监控
v=DMARC1; p=none; rua=mailto:dmarc-reports@neshama.ai; ruf=mailto:dmarc-reports@neshama.ai; pct=100

# 阶段2：隔离可疑邮件
v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@neshama.ai; ruf=mailto:dmarc-reports@neshama.ai; pct=100

# 阶段3：拒绝可疑邮件（谨慎使用）
v=DMARC1; p=reject; rua=mailto:dmarc-reports@neshama.ai; ruf=mailto:dmarc-reports@neshama.ai; pct=100
```

---

## �Step 5: 验证配置

### 在线验证工具

1. **MXToolbox**
   - https://mxtoolbox.com/SuperTool.aspx
   
2. **验证 SPF**
   - 输入: `nslookup -type=txt neshama.ai`
   
3. **验证 DKIM**
   - 输入: `nslookup -type=txt selector._domainkey.neshama.ai`
   
4. **验证 DMARC**
   - 输入: `nslookup -type=txt _dmarc.neshama.ai`

### 发送测试邮件

1. 使用邮件服务商的控制台发送测试邮件
2. 发送至 test@mail-tester.com
3. 检查返回的评分和详细报告

---

## 📧 Neshama AI 邮箱地址

配置完成后，以下邮箱地址将正常工作：

| 用途 | 邮箱地址 |
|-----|---------|
| 隐私政策联系 | privacy@neshama.ai |
| 服务条款联系 | legal@neshama.ai |
| 退款申请 | support@neshama.ai |
| 一般支持 | support@neshama.ai |
| DMARC 报告 | dmarc-reports@neshama.ai |

---

## 🔧 常见问题

### Q: SPF 记录添加后多久生效？
**A:** 通常 5-30 分钟，但完全生效可能需要 24-48 小时。

### Q: 可以同时使用多个邮件服务商吗？
**A:** 可以，但需要将所有服务商的 include 语句合并到一个 SPF 记录中。

### Q: DKIM 签名为什么不生效？
**A:** 检查以下几点：
1. DNS 记录是否正确添加
2. 选择器（selector）是否与服务商提供的一致
3. 是否等待了足够的 DNS 传播时间

### Q: DMARC 报告收到大量失败？
**A:** 检查报告中的失败原因：
- `SPF` 失败 → SPF 记录配置问题
- `DKIM` 失败 → DKIM 签名未正确添加

### Q: 邮件还是进入垃圾箱？
**A:** 除了 DNS 记录，还需要：
- 确保发送内容不包含垃圾邮件特征
- 维护良好的发件人信誉
- 定期清理无效邮件地址

---

## 📞 获取帮助

如有疑问，请联系邮件服务提供商的技术支持，或查阅：

- [SendGrid SPF/DKIM 配置指南](https://sendgrid.com/docs/ui/account-and-settings/dkim-authentication/)
- [Amazon SES DKIM 配置](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/set-up-dkim.html)
- [DMARC 官方文档](https://dmarc.org/overview/)

---

*最后更新：2026年3月*
