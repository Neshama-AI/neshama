/**
 * Privacy Policy Page - GDPR/CCPA Compliant Privacy Policy
 */

const PRIVACY_TOC = [
    { id: 'information-controller', key: 'privacy.toc.infoController' },
    { id: 'data-we-collect', key: 'privacy.toc.dataCollect' },
    { id: 'purpose-processing', key: 'privacy.toc.purpose' },
    { id: 'data-storage', key: 'privacy.toc.storage' },
    { id: 'data-retention', key: 'privacy.toc.retention' },
    { id: 'user-rights', key: 'privacy.toc.rights' },
    { id: 'cookies', key: 'privacy.toc.cookies' },
    { id: 'third-party', key: 'privacy.toc.thirdParty' },
    { id: 'data-transfer', key: 'privacy.toc.transfer' },
    { id: 'children-privacy', key: 'privacy.toc.children' },
    { id: 'policy-updates', key: 'privacy.toc.updates' },
    { id: 'contact-us', key: 'privacy.toc.contact' }
];

const LAST_UPDATED = '2026-03-01';

// Privacy Policy Content - Chinese
const privacyContentZh = {
    'information-controller': {
        title: '一、信息控制者',
        content: `<p><strong>Neshama AI</strong>（以下简称"Neshama"、"我们"或"我们的"）是您在使用我们的NPC灵魂操作系统（以下简称"服务"）时所提供个人数据的控制者。</p>
        <p><strong>注册地址：</strong>美国特拉华州（具体地址请联系 privacy@neshama.ai）</p>
        <p><strong>联系邮箱：</strong>privacy@neshama.ai</p>
        <p>如果您对本隐私政策有任何疑问，或希望行使您的数据保护权利，请通过上述邮箱与我们联系。</p>`
    },
    'data-we-collect': {
        title: '二、我们收集的数据',
        content: `<p>我们收集以下类型的个人数据以提供服务：</p>
        <ul>
            <li><strong>账户信息：</strong>电子邮箱地址、密码（加密存储）、账户偏好设置</li>
            <li><strong>NPC人格配置：</strong>您创建的NPC角色名称、人格特质参数（OCEAN模型参数）、行为配置、记忆配置</li>
            <li><strong>对话记录：</strong>您与NPC之间的对话内容、聊天时间戳</li>
            <li><strong>情绪状态数据：</strong>NPC的情绪状态历史、情绪触发事件、情绪强度曲线</li>
            <li><strong>实体图谱数据：</strong>NPC认知中的实体、实体关系、知识图谱</li>
            <li><strong>使用统计：</strong>API调用次数、会话时长、功能使用频率、错误日志</li>
            <li><strong>支付信息：</strong>通过第三方支付处理（Stripe），我们不存储您的完整信用卡信息</li>
        </ul>
        <p class="note"><strong>注意：</strong>NPC生成的对话内容由人工智能模型自动创建，不代表Neshama的立场或观点。</p>`
    },
    'purpose-processing': {
        title: '三、数据处理目的',
        content: `<p>我们仅在以下目的下处理您的个人数据：</p>
        <ul>
            <li><strong>提供服务：</strong>运行NPC灵魂操作系统，提供人格配置、对话生成、情绪模拟、记忆管理等功能</li>
            <li><strong>账户管理：</strong>创建和管理用户账户、处理用户认证</li>
            <li><strong>服务改进：</strong>分析使用数据以改进服务质量、修复bug、优化性能</li>
            <li><strong>计费和支付：</strong>处理订阅费用、执行退款（如适用）</li>
            <li><strong>安全监控：</strong>检测和预防欺诈、滥用和非法活动</li>
            <li><strong>法律合规：</strong>遵守适用法律法规，配合执法机构要求</li>
        </ul>
        <p>我们处理数据的法律依据包括：履行合同（服务条款）、您的同意、以及我们的合法利益（如服务安全和改进）。</p>`
    },
    'data-storage': {
        title: '四、数据存储与安全',
        content: `<p><strong>存储位置：</strong>您的个人数据存储在云端服务器上。我们使用行业标准的安全措施保护您的数据，包括但不限于：</p>
        <ul>
            <li>AES-256加密存储敏感数据</li>
            <li>传输层TLS 1.3加密所有网络通信</li>
            <li>定期安全审计和渗透测试</li>
            <li>严格的访问控制和身份验证</li>
            <li>数据中心采用物理安全措施</li>
        </ul>
        <p>我们将采取一切合理措施确保您的个人数据得到安全处理，并符合GDPR和CCPA的要求。</p>`
    },
    'data-retention': {
        title: '五、数据保留期限',
        content: `<p>我们将根据以下规则保留您的个人数据：</p>
        <ul>
            <li><strong>活跃账户：</strong>您的个人数据将在您的账户保持活跃期间被保留</li>
            <li><strong>删除后30天：</strong>当您请求删除账户或数据时，我们将在30天内完成删除操作</li>
            <li><strong>法定保留：</strong>某些数据可能因法律要求需要保留更长时间（如税务记录保留7年）</li>
            <li><strong>匿名化数据：</strong>用于分析和服务改进的匿名化数据可能被无限期保留</li>
        </ul>
        <p class="important"><strong>重要：</strong>账户删除后，我们提供30天的数据恢复宽限期。在此期间，您可以联系 support@neshama.ai 恢复您的账户和数据。</p>`
    },
    'user-rights': {
        title: '六、您的权利',
        content: `<p>根据GDPR和CCPA，您享有以下权利：</p>
        <h4>GDPR权利（欧盟用户）</h4>
        <ul>
            <li><strong>访问权：</strong>了解我们持有的关于您的个人数据</li>
            <li><strong>更正权：</strong>要求更正不准确的个人数据</li>
            <li><strong>删除权：</strong>要求删除您的个人数据（"被遗忘权"）</li>
            <li><strong>数据可携带权：</strong>获取您的个人数据的机器可读副本</li>
            <li><strong>限制处理权：</strong>限制我们对您数据的某些处理活动</li>
            <li><strong>撤回同意权：</strong>随时撤回您之前给予的同意</li>
            <li><strong>反对权：</strong>反对我们基于合法利益处理您的数据</li>
        </ul>
        <h4>CCPA权利（加州用户）</h4>
        <ul>
            <li><strong>知情权：</strong>了解我们收集、使用和共享的个人信息</li>
            <li><strong>删除权：</strong>要求删除您的个人信息</li>
            <li><strong>选择退出权：</strong>选择退出个人信息被"出售"（我们不出售您的数据）</li>
            <li><strong>非歧视权：</strong>不会因行使CCPA权利而受到歧视</li>
        </ul>
        <p>如需行使上述任何权利，请发送邮件至 privacy@neshama.ai。我们将在30天内响应您的请求。</p>`
    },
    'cookies': {
        title: '七、Cookie使用政策',
        content: `<p>我们仅使用以下必要的Cookie来确保服务正常运行：</p>
        <table class="legal-table">
            <thead>
                <tr>
                    <th>Cookie名称</th>
                    <th>用途</th>
                    <th>类型</th>
                    <th>过期时间</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>session_id</td>
                    <td>维护用户会话状态</td>
                    <td>必要</td>
                    <td>会话结束</td>
                </tr>
                <tr>
                    <td>neshama-lang</td>
                    <td>保存语言偏好设置</td>
                    <td>功能</td>
                    <td>1年</td>
                </tr>
                <tr>
                    <td>theme</td>
                    <td>保存界面主题偏好</td>
                    <td>功能</td>
                    <td>1年</td>
                </tr>
            </tbody>
        </table>
        <p>我们不使用跟踪性Cookie或广告Cookie。您可以通过浏览器设置管理Cookie偏好，但这可能影响某些功能。</p>`
    },
    'third-party': {
        title: '八、第三方服务',
        content: `<p>为提供服务，我们使用以下第三方服务提供商：</p>
        <ul>
            <li><strong>LLM提供商：</strong>OpenAI、DeepSeek等用于生成NPC对话和人格模拟</li>
            <li><strong>云服务：</strong>AWS、Google Cloud或Azure用于数据存储和计算</li>
            <li><strong>支付处理：</strong>Stripe用于处理订阅付款</li>
            <li><strong>数据分析：</strong>用于服务分析和改进的匿名化数据</li>
        </ul>
        <p>所有第三方提供商都受到适当的数据处理协议约束，并符合GDPR和CCPA的要求。我们建议您阅读这些第三方的隐私政策。</p>`
    },
    'data-transfer': {
        title: '九、国际数据传输',
        content: `<p>我们的服务可能在全球范围内提供，您的数据可能会被传输到您所在国家/地区以外的服务进行处理。</p>
        <p>当进行国际数据传输时，我们确保采取以下措施保护您的数据：</p>
        <ul>
            <li>使用欧盟委员会批准的标准合同条款（SCCs）</li>
            <li>确保目的地国家/地区提供足够的数据保护水平</li>
            <li>实施技术安全措施（如加密）保护传输中的数据</li>
        </ul>
        <p>通过使用我们的服务，您同意在您所在司法管辖区之外传输和处理您的个人数据。</p>`
    },
    'children-privacy': {
        title: '十、儿童隐私',
        content: `<p><strong>我们的服务不面向13岁以下（或您所在国家/地区规定的同等年龄）的儿童。</strong></p>
        <p>我们不会故意收集13岁以下儿童的个人信息。如果我们发现无意中收集了儿童的个人信息，我们将立即采取措施删除该信息。</p>
        <p>如果您是家长或监护人，并认为您的孩子可能向我们提供了个人信息，请通过 privacy@neshama.ai 联系我们。</p>`
    },
    'policy-updates': {
        title: '十一、隐私政策更新',
        content: `<p>我们可能会不时更新本隐私政策以反映服务、法律或监管的变化。</p>
        <p><strong>更新通知：</strong></p>
        <ul>
            <li>我们将在更改生效前至少30天通过电子邮件通知您</li>
            <li>重大变更将在我们的网站上发布通知</li>
            <li>更新后的政策将在页眉标注新的"最后更新"日期</li>
        </ul>
        <p>如果您在政策更新后继续使用我们的服务，即表示您接受更新后的隐私政策。</p>`
    },
    'contact-us': {
        title: '十二、联系我们',
        content: `<p>如果您对本隐私政策有任何疑问、意见或请求，请通过以下方式联系我们：</p>
        <ul>
            <li><strong>隐私相关：</strong>privacy@neshama.ai</li>
            <li><strong>一般支持：</strong>support@neshama.ai</li>
        </ul>
        <p>我们将尽最大努力在30天内回复您的询问。</p>
        <p><strong>数据保护官：</strong>如需联系我们的数据保护官，请发送邮件至 privacy@neshama.ai，邮件主题请注明"Attn: DPO"。</p>`
    }
};

// Privacy Policy Content - English
const privacyContentEn = {
    'information-controller': {
        title: '1. Information Controller',
        content: `<p><strong>Neshama AI</strong> ("Neshama", "we", or "our") is the controller of your personal data when you use our NPC Soul Operating System (the "Service").</p>
        <p><strong>Registered Address:</strong> Delaware, USA (contact privacy@neshama.ai for details)</p>
        <p><strong>Contact Email:</strong> privacy@neshama.ai</p>
        <p>If you have any questions about this Privacy Policy or wish to exercise your data protection rights, please contact us at the email above.</p>`
    },
    'data-we-collect': {
        title: '2. Data We Collect',
        content: `<p>We collect the following types of personal data to provide the Service:</p>
        <ul>
            <li><strong>Account Information:</strong> Email address, password (encrypted), account preferences</li>
            <li><strong>NPC Personality Configurations:</strong> NPC character names you create, personality trait parameters (OCEAN model), behavior configurations, memory settings</li>
            <li><strong>Chat History:</strong> Conversations between you and NPCs, chat timestamps</li>
            <li><strong>Emotion State Data:</strong> NPC emotion state history, emotion-triggering events, emotion intensity curves</li>
            <li><strong>Entity Graph Data:</strong> Entities in NPC cognition, entity relationships, knowledge graphs</li>
            <li><strong>Usage Statistics:</strong> API call counts, session duration, feature usage frequency, error logs</li>
            <li><strong>Payment Information:</strong> Processed through third-party payment processor (Stripe); we do not store your complete credit card information</li>
        </ul>
        <p class="note"><strong>Note:</strong> NPC-generated conversation content is automatically created by AI models and does not represent Neshama's position or views.</p>`
    },
    'purpose-processing': {
        title: '3. Purpose of Data Processing',
        content: `<p>We process your personal data only for the following purposes:</p>
        <ul>
            <li><strong>Service Provision:</strong> Operating the NPC Soul Operating System, providing personality configuration, conversation generation, emotion simulation, and memory management</li>
            <li><strong>Account Management:</strong> Creating and managing user accounts, handling user authentication</li>
            <li><strong>Service Improvement:</strong> Analyzing usage data to improve service quality, fix bugs, optimize performance</li>
            <li><strong>Billing and Payments:</strong> Processing subscription fees, executing refunds (if applicable)</li>
            <li><strong>Security Monitoring:</strong> Detecting and preventing fraud, abuse, and illegal activities</li>
            <li><strong>Legal Compliance:</strong> Complying with applicable laws and regulations, cooperating with law enforcement</li>
        </ul>
        <p>The legal basis for our data processing includes: contract performance (Terms of Service), your consent, and our legitimate interests (such as service security and improvement).</p>`
    },
    'data-storage': {
        title: '4. Data Storage and Security',
        content: `<p><strong>Storage Location:</strong> Your personal data is stored on cloud servers. We use industry-standard security measures to protect your data, including but not limited to:</p>
        <ul>
            <li>AES-256 encryption for sensitive data storage</li>
            <li>TLS 1.3 encryption for all network communications</li>
            <li>Regular security audits and penetration testing</li>
            <li>Strict access controls and authentication</li>
            <li>Physical security measures at data centers</li>
        </ul>
        <p>We will take all reasonable measures to ensure your personal data is handled securely and in compliance with GDPR and CCPA requirements.</p>`
    },
    'data-retention': {
        title: '5. Data Retention Period',
        content: `<p>We retain your personal data according to the following rules:</p>
        <ul>
            <li><strong>Active Accounts:</strong> Your personal data is retained while your account remains active</li>
            <li><strong>30 Days After Deletion:</strong> When you request account or data deletion, we complete the deletion within 30 days</li>
            <li><strong>Legal Retention:</strong> Certain data may be retained longer due to legal requirements (e.g., tax records retained for 7 years)</li>
            <li><strong>Anonymized Data:</strong> Anonymized data used for analytics and service improvement may be retained indefinitely</li>
        </ul>
        <p class="important"><strong>Important:</strong> After account deletion, we provide a 30-day grace period for data recovery. During this period, you can contact support@neshama.ai to restore your account and data.</p>`
    },
    'user-rights': {
        title: '6. Your Rights',
        content: `<p>Under GDPR and CCPA, you have the following rights:</p>
        <h4>GDPR Rights (EU Users)</h4>
        <ul>
            <li><strong>Right of Access:</strong> Know what personal data we hold about you</li>
            <li><strong>Right to Rectification:</strong> Request correction of inaccurate personal data</li>
            <li><strong>Right to Erasure:</strong> Request deletion of your personal data ("Right to be Forgotten")</li>
            <li><strong>Right to Data Portability:</strong> Obtain a machine-readable copy of your personal data</li>
            <li><strong>Right to Restrict Processing:</strong> Limit certain processing activities on your data</li>
            <li><strong>Right to Withdraw Consent:</strong> Withdraw consent you previously gave at any time</li>
            <li><strong>Right to Object:</strong> Object to processing based on legitimate interests</li>
        </ul>
        <h4>CCPA Rights (California Users)</h4>
        <ul>
            <li><strong>Right to Know:</strong> Understand what personal information we collect, use, and share</li>
            <li><strong>Right to Delete:</strong> Request deletion of your personal information</li>
            <li><strong>Right to Opt-Out:</strong> Opt-out of personal information being "sold" (we do not sell your data)</li>
            <li><strong>Right to Non-Discrimination:</strong> Not be discriminated against for exercising CCPA rights</li>
        </ul>
        <p>To exercise any of these rights, please send an email to privacy@neshama.ai. We will respond to your request within 30 days.</p>`
    },
    'cookies': {
        title: '7. Cookie Policy',
        content: `<p>We use only the following essential cookies to ensure proper service functionality:</p>
        <table class="legal-table">
            <thead>
                <tr>
                    <th>Cookie Name</th>
                    <th>Purpose</th>
                    <th>Type</th>
                    <th>Expiration</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>session_id</td>
                    <td>Maintain user session state</td>
                    <td>Essential</td>
                    <td>Session end</td>
                </tr>
                <tr>
                    <td>neshama-lang</td>
                    <td>Save language preference</td>
                    <td>Functional</td>
                    <td>1 year</td>
                </tr>
                <tr>
                    <td>theme</td>
                    <td>Save interface theme preference</td>
                    <td>Functional</td>
                    <td>1 year</td>
                </tr>
            </tbody>
        </table>
        <p>We do not use tracking cookies or advertising cookies. You can manage cookie preferences through your browser settings, though this may affect certain functionality.</p>`
    },
    'third-party': {
        title: '8. Third-Party Services',
        content: `<p>To provide the Service, we use the following third-party service providers:</p>
        <ul>
            <li><strong>LLM Providers:</strong> OpenAI, DeepSeek, etc. for generating NPC conversations and personality simulation</li>
            <li><strong>Cloud Services:</strong> AWS, Google Cloud, or Azure for data storage and computing</li>
            <li><strong>Payment Processing:</strong> Stripe for handling subscription payments</li>
            <li><strong>Data Analytics:</strong> Anonymized data for service analysis and improvement</li>
        </ul>
        <p>All third-party providers are bound by appropriate data processing agreements and comply with GDPR and CCPA requirements. We recommend you review these third parties' privacy policies.</p>`
    },
    'data-transfer': {
        title: '9. International Data Transfers',
        content: `<p>Our Service may be provided globally, and your data may be transferred to and processed in countries other than your own.</p>
        <p>When making international data transfers, we ensure the following measures protect your data:</p>
        <ul>
            <li>Using Standard Contractual Clauses (SCCs) approved by the European Commission</li>
            <li>Ensuring adequate data protection levels in destination countries/regions</li>
            <li>Implementing technical security measures (such as encryption) for data in transit</li>
        </ul>
        <p>By using our Service, you consent to the transfer and processing of your personal data outside your jurisdiction.</p>`
    },
    'children-privacy': {
        title: "10. Children's Privacy",
        content: `<p><strong>Our Service is not intended for children under 13 years of age (or the equivalent age in your country).</strong></p>
        <p>We do not knowingly collect personal information from children under 13. If we discover that we have inadvertently collected a child's personal information, we will take immediate steps to delete that information.</p>
        <p>If you are a parent or guardian and believe your child may have provided us with personal information, please contact us at privacy@neshama.ai.</p>`
    },
    'policy-updates': {
        title: '11. Privacy Policy Updates',
        content: `<p>We may update this Privacy Policy from time to time to reflect changes in our Service, laws, or regulations.</p>
        <p><strong>Update Notifications:</strong></p>
        <ul>
            <li>We will notify you via email at least 30 days before changes take effect</li>
            <li>Significant changes will be posted on our website</li>
            <li>Updated policy will show a new "Last Updated" date in the header</li>
        </ul>
        <p>If you continue to use our Service after the policy update, you accept the updated Privacy Policy.</p>`
    },
    'contact-us': {
        title: '12. Contact Us',
        content: `<p>If you have any questions, comments, or requests regarding this Privacy Policy, please contact us:</p>
        <ul>
            <li><strong>Privacy Related:</strong> privacy@neshama.ai</li>
            <li><strong>General Support:</strong> support@neshama.ai</li>
        </ul>
        <p>We will endeavor to respond to your inquiries within 30 days.</p>
        <p><strong>Data Protection Officer:</strong> To contact our DPO, please send an email to privacy@neshama.ai with "Attn: DPO" in the subject line.</p>`
    }
};

// Render Privacy Policy Page
async function renderPrivacy() {
    const container = document.getElementById('page-privacy');
    const isZh = getCurrentLang() === 'zh';
    const content = isZh ? privacyContentZh : privacyContentEn;
    const toc = PRIVACY_TOC;

    container.innerHTML = `
        <div class="legal-page">
            <div class="legal-header">
                <div class="legal-title-row">
                    <h1 class="legal-title">${isZh ? '隐私政策' : 'Privacy Policy'}</h1>
                    <div class="legal-lang-toggle">
                        <button class="lang-btn ${isZh ? 'active' : ''}" onclick="setLang('zh')">中文</button>
                        <button class="lang-btn ${!isZh ? 'active' : ''}" onclick="setLang('en')">EN</button>
                    </div>
                </div>
                <p class="legal-last-updated">
                    ${isZh ? '最后更新' : 'Last Updated'}: ${LAST_UPDATED}
                </p>
            </div>
            
            <div class="legal-content-wrapper">
                <nav class="legal-toc">
                    <h2 class="toc-title">${isZh ? '目录' : 'Table of Contents'}</h2>
                    <ul class="toc-list">
                        ${toc.map(item => `
                            <li>
                                <a href="#${item.id}" class="toc-link" data-section="${item.id}">
                                    ${t(item.key)}
                                </a>
                            </li>
                        `).join('')}
                    </ul>
                </nav>
                
                <div class="legal-content">
                    ${toc.map(item => `
                        <section id="${item.id}" class="legal-section">
                            <h2 class="section-title">${content[item.id].title}</h2>
                            <div class="section-content">
                                ${content[item.id].content}
                            </div>
                        </section>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    // Setup smooth scroll for TOC links
    setTimeout(() => {
        document.querySelectorAll('.toc-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }, 100);
}
