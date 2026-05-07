/**
 * Refund Policy Page - Detailed Refund Terms and Process
 */

const REFUND_TOC = [
    { id: 'refund-overview', key: 'refund.toc.overview' },
    { id: 'eligibility', key: 'refund.toc.eligibility' },
    { id: 'non-refundable', key: 'refund.toc.nonRefund' },
    { id: 'refund-process', key: 'refund.toc.process' },
    { id: 'data-after-refund', key: 'refund.toc.dataAfter' },
    { id: 'faq', key: 'refund.toc.faq' },
    { id: 'contact', key: 'refund.toc.contact' }
];

const REFUND_LAST_UPDATED = '2026-03-01';

// Refund Policy Content - Chinese
const refundContentZh = {
    'refund-overview': {
        title: '一、退款政策概述',
        content: `<p>Neshama AI 致力于为用户提供优质的服务体验。我们理解您可能因各种原因需要退款，因此我们制定了以下退款政策。</p>
        
        <div class="refund-highlight">
            <h4>核心退款政策</h4>
            <ul>
                <li><strong>首次订阅：</strong>14天内无理由全额退款</li>
                <li><strong>续费订阅：</strong>按剩余天数比例退款</li>
                <li><strong>退款处理：</strong>1-3个工作日完成</li>
                <li><strong>退款方式：</strong>原路返回</li>
            </ul>
        </div>
        
        <p>如果您对本退款政策有任何疑问，请联系我们的支持团队。</p>`
    },
    'eligibility': {
        title: '二、退款条件',
        content: `<h4>首次订阅退款（14天无理由退款）</h4>
        <p>如果您是首次订阅 Neshama 服务，并且在订阅后14天内申请退款，您将有资格获得全额退款。</p>
        <ul>
            <li>适用对象：首次订阅用户</li>
            <li>申请期限：订阅后14天内</li>
            <li>退款金额：100%订阅费用</li>
            <li>无需提供退款理由</li>
        </ul>
        
        <h4>续费订阅退款（按比例退款）</h4>
        <p>如果您已使用服务超过14天，退款将按剩余未使用的订阅天数比例计算。</p>
        <ul>
            <li>计算公式：(未使用天数 / 总订阅天数) × 已支付金额</li>
            <li>最低退款金额：$1.00（低于此金额将不予处理）</li>
            <li>退款申请必须在当前计费周期结束前提交</li>
        </ul>
        
        <h4>特殊情况</h4>
        <p>以下情况可申请全额退款，即使超过14天：</p>
        <ul>
            <li>服务连续中断超过72小时（非计划维护）</li>
            <li>因服务重大变更导致功能不可用</li>
            <li>系统错误导致重复扣费</li>
        </ul>`
    },
    'non-refundable': {
        title: '三、不支持退款的项目',
        content: `<p>以下购买项目<strong>不支持退款</strong>：</p>
        
        <h4>一次性购买项目</h4>
        <ul>
            <li><strong>额外NPC包：</strong>购买的额外NPC数量包不支持退款</li>
            <li><strong>交互包：</strong>一次性购买的交互次数包不支持退款</li>
            <li><strong>API调用包：</strong>预付费的API调用额度不支持退款</li>
        </ul>
        
        <h4>其他不支持情况</h4>
        <ul>
            <li>已使用超过30天的订阅</li>
            <li>因用户违反服务条款导致账户被暂停或终止</li>
            <li>用户主动删除账户后的订阅费用</li>
            <li>通过优惠码或赠品获得的订阅</li>
            <li>第三方销售渠道购买的订阅（如有特殊政策例外）</li>
        </ul>
        
        <div class="refund-warning">
            <p><strong>重要提示：</strong>在申请退款前，请确保您了解上述不支持退款的项目。一旦退款申请被受理，相关服务访问权限将被立即终止。</p>
        </div>`
    },
    'refund-process': {
        title: '四、退款流程',
        content: `<h4>退款申请步骤</h4>
        <div class="refund-steps">
            <div class="refund-step">
                <div class="step-number">1</div>
                <div class="step-content">
                    <h5>联系支持团队</h5>
                    <p>发送邮件至 <a href="mailto:support@neshama.ai">support@neshama.ai</a>，邮件主题请注明"退款申请"</p>
                </div>
            </div>
            <div class="refund-step">
                <div class="step-number">2</div>
                <div class="step-content">
                    <h5>提供必要信息</h5>
                    <p>在邮件中提供以下信息：</p>
                    <ul>
                        <li>注册邮箱地址</li>
                        <li>订阅类型和订阅日期</li>
                        <li>退款原因（首次订阅14天内无需提供）</li>
                    </ul>
                </div>
            </div>
            <div class="refund-step">
                <div class="step-number">3</div>
                <div class="step-content">
                    <h5>等待审核</h5>
                    <p>我们的团队将在1-3个工作日内审核您的申请。</p>
                </div>
            </div>
            <div class="refund-step">
                <div class="step-number">4</div>
                <div class="step-content">
                    <h5>退款处理</h5>
                    <p>审核通过后，退款将原路返回到您的支付账户。</p>
                </div>
            </div>
        </div>
        
        <h4>退款时间表</h4>
        <table class="legal-table">
            <thead>
                <tr>
                    <th>阶段</th>
                    <th>预计时间</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>申请提交</td>
                    <td>即时</td>
                    <td>收到您的退款申请邮件</td>
                </tr>
                <tr>
                    <td>审核处理</td>
                    <td>1-3个工作日</td>
                    <td>我们审核您的退款资格</td>
                </tr>
                <tr>
                    <td>退款执行</td>
                    <td>5-10个工作日</td>
                    <td>资金退回您的账户</td>
                </tr>
                <tr>
                    <td>总计</td>
                    <td>最长14个工作日</td>
                    <td>从申请到完成</td>
                </tr>
            </tbody>
        </table>`
    },
    'data-after-refund': {
        title: '五、退款后数据处理',
        content: `<p>当您的退款申请被受理后，我们将按照以下流程处理您的数据：</p>
        
        <h4>退款后数据保留政策</h4>
        <div class="refund-data-timeline">
            <div class="timeline-item">
                <div class="timeline-date">退款完成</div>
                <div class="timeline-content">
                    <p>服务访问权限立即终止</p>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">0-30天</div>
                <div class="timeline-content">
                    <p><strong>数据保留期</strong></p>
                    <p>您的账户数据（包括NPC配置、对话记录、记忆等）将在服务器上保留30天。</p>
                    <p>在此期间，您可以联系 support@neshama.ai 恢复您的账户。</p>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">30天后</div>
                <div class="timeline-content">
                    <p><strong>永久删除</strong></p>
                    <p>所有数据将被永久删除，无法恢复。</p>
                </div>
            </div>
        </div>
        
        <h4>数据恢复选项</h4>
        <p>如果您改变主意并希望继续使用服务：</p>
        <ul>
            <li>在30天保留期内联系我们</li>
            <li>重新订阅服务</li>
            <li>您的数据将完全恢复</li>
        </ul>
        
        <div class="refund-warning">
            <p><strong>注意：</strong>如果您希望彻底删除所有数据而不保留恢复选项，请在退款申请中明确说明"永久删除所有数据"。</p>
        </div>`
    },
    'faq': {
        title: '六、常见问题',
        content: `<div class="refund-faq">
            <div class="faq-item">
                <h4>问：退款后我还能重新订阅吗？</h4>
                <p>答：是的，您可以随时重新订阅。但请注意，重新订阅将被视为新订阅，而非续费。</p>
            </div>
            
            <div class="faq-item">
                <h4>问：退款需要多长时间才能到账？</h4>
                <p>答：一般情况下，从申请到到账需要5-10个工作日。具体时间取决于您的银行或支付机构。</p>
            </div>
            
            <div class="faq-item">
                <h4>问：如果我使用了免费试用，还能申请退款吗？</h4>
                <p>答：如果您在免费试用期内订阅付费计划，14天退款政策仍然适用。</p>
            </div>
            
            <div class="faq-item">
                <h4>问：退款后如何处理我创建的NPC？</h4>
                <p>答：在30天保留期内，您可以恢复账户并继续使用所有NPC。30天后，所有NPC数据将被永久删除。</p>
            </div>
            
            <div class="faq-item">
                <h4>问：我不满意服务，可以投诉吗？</h4>
                <p>答：当然可以。我们非常重视用户反馈。请联系 support@neshama.ai 说明您的问题，我们会尽力解决。</p>
            </div>
            
            <div class="faq-item">
                <h4>问： Stripe收取的手续费会退还吗？</h4>
                <p>答：退款金额将基于您实际支付的订阅费用。Stripe的手续费可能不包含在退款金额中，具体取决于Stripe的政策。</p>
            </div>
        </div>`
    },
    'contact': {
        title: '七、联系我们',
        content: `<p>如果您有任何关于退款的问题，请通过以下方式联系我们：</p>
        
        <div class="contact-methods">
            <div class="contact-item">
                <h4>退款申请邮箱</h4>
                <p><a href="mailto:support@neshama.ai">support@neshama.ai</a></p>
                <p class="contact-note">请在邮件主题中注明"退款申请"</p>
            </div>
            
            <div class="contact-item">
                <h4>响应时间</h4>
                <p>工作日：周一至周五 9:00-18:00（北京时间）</p>
                <p>我们将在1-3个工作日内回复您的邮件</p>
            </div>
            
            <div class="contact-item">
                <h4>退款查询</h4>
                <p>如果您已提交退款申请并超过14个工作日未收到退款，请提供以下信息联系我们：</p>
                <ul>
                    <li>退款申请日期</li>
                    <li>申请时使用的邮箱</li>
                    <li>退款参考编号（如有）</li>
                </ul>
            </div>
        </div>
        
        <div class="refund-related-links">
            <h4>相关链接</h4>
            <ul>
                <li><a href="#" onclick="navigateTo('terms')">服务条款</a></li>
                <li><a href="#" onclick="navigateTo('privacy')">隐私政策</a></li>
                <li><a href="mailto:support@neshama.ai">联系支持团队</a></li>
            </ul>
        </div>`
    }
};

// Refund Policy Content - English
const refundContentEn = {
    'refund-overview': {
        title: '1. Refund Policy Overview',
        content: `<p>Neshama AI is committed to providing users with an excellent service experience. We understand that you may need a refund for various reasons, so we have established the following refund policy.</p>
        
        <div class="refund-highlight">
            <h4>Core Refund Policy</h4>
            <ul>
                <li><strong>First Subscription:</strong> Full refund within 14 days, no questions asked</li>
                <li><strong>Renewed Subscription:</strong> Prorated refund based on remaining days</li>
                <li><strong>Processing Time:</strong> 1-3 business days</li>
                <li><strong>Refund Method:</strong> Original payment method</li>
            </ul>
        </div>
        
        <p>If you have any questions about this refund policy, please contact our support team.</p>`
    },
    'eligibility': {
        title: '2. Refund Eligibility',
        content: `<h4>First Subscription Refund (14-Day Money-Back Guarantee)</h4>
        <p>If you are subscribing to Neshama for the first time and request a refund within 14 days of subscribing, you are eligible for a full refund.</p>
        <ul>
            <li>Eligible: First-time subscribers only</li>
            <li>Request Period: Within 14 days of subscription</li>
            <li>Refund Amount: 100% of subscription fee</li>
            <li>No reason required</li>
        </ul>
        
        <h4>Renewed Subscription Refund (Prorated)</h4>
        <p>If you have been using the service for more than 14 days, the refund will be calculated based on the remaining unused subscription days.</p>
        <ul>
            <li>Formula: (Unused days / Total subscription days) × Amount paid</li>
            <li>Minimum refund: $1.00 (requests below this amount will not be processed)</li>
            <li>Refund requests must be submitted before the end of the current billing cycle</li>
        </ul>
        
        <h4>Special Circumstances</h4>
        <p>Full refunds may be granted in the following situations, even after 14 days:</p>
        <ul>
            <li>Service interruption exceeding 72 consecutive hours (excluding scheduled maintenance)</li>
            <li>Service unavailable due to significant service changes</li>
            <li>Duplicate charges due to system errors</li>
        </ul>`
    },
    'non-refundable': {
        title: '3. Non-Refundable Items',
        content: `<p>The following purchase items are <strong>non-refundable</strong>:</p>
        
        <h4>One-Time Purchases</h4>
        <ul>
            <li><strong>Additional NPC Packs:</strong> Purchased additional NPC quantity packs are non-refundable</li>
            <li><strong>Interaction Packs:</strong> One-time purchased interaction credits are non-refundable</li>
            <li><strong>API Call Packs:</strong> Prepaid API call credits are non-refundable</li>
        </ul>
        
        <h4>Other Non-Refundable Situations</h4>
        <ul>
            <li>Subscriptions used for more than 30 days</li>
            <li>Account suspended or terminated due to violation of Terms of Service</li>
            <li>Subscription fees after user-initiated account deletion</li>
            <li>Subscriptions obtained through promotional codes or gifts</li>
            <li>Subscriptions purchased through third-party sales channels (unless special policy applies)</li>
        </ul>
        
        <div class="refund-warning">
            <p><strong>Important:</strong> Before requesting a refund, please ensure you understand the non-refundable items above. Once a refund request is accepted, service access will be immediately terminated.</p>
        </div>`
    },
    'refund-process': {
        title: '4. Refund Process',
        content: `<h4>Refund Request Steps</h4>
        <div class="refund-steps">
            <div class="refund-step">
                <div class="step-number">1</div>
                <div class="step-content">
                    <h5>Contact Support Team</h5>
                    <p>Send an email to <a href="mailto:support@neshama.ai">support@neshama.ai</a> with "Refund Request" in the subject line</p>
                </div>
            </div>
            <div class="refund-step">
                <div class="step-number">2</div>
                <div class="step-content">
                    <h5>Provide Required Information</h5>
                    <p>Include the following in your email:</p>
                    <ul>
                        <li>Registered email address</li>
                        <li>Subscription type and subscription date</li>
                        <li>Reason for refund (not required for first subscription within 14 days)</li>
                    </ul>
                </div>
            </div>
            <div class="refund-step">
                <div class="step-number">3</div>
                <div class="step-content">
                    <h5>Wait for Review</h5>
                    <p>Our team will review your request within 1-3 business days.</p>
                </div>
            </div>
            <div class="refund-step">
                <div class="step-number">4</div>
                <div class="step-content">
                    <h5>Refund Processed</h5>
                    <p>Once approved, the refund will be returned to your original payment method.</p>
                </div>
            </div>
        </div>
        
        <h4>Refund Timeline</h4>
        <table class="legal-table">
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Estimated Time</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Request Submission</td>
                    <td>Immediate</td>
                    <td>We receive your refund request email</td>
                </tr>
                <tr>
                    <td>Review Processing</td>
                    <td>1-3 business days</td>
                    <td>We verify your refund eligibility</td>
                </tr>
                <tr>
                    <td>Refund Execution</td>
                    <td>5-10 business days</td>
                    <td>Funds returned to your account</td>
                </tr>
                <tr>
                    <td>Total</td>
                    <td>Up to 14 business days</td>
                    <td>From request to completion</td>
                </tr>
            </tbody>
        </table>`
    },
    'data-after-refund': {
        title: '5. Data Handling After Refund',
        content: `<p>Once your refund request is accepted, we will process your data according to the following procedure:</p>
        
        <h4>Post-Refund Data Retention Policy</h4>
        <div class="refund-data-timeline">
            <div class="timeline-item">
                <div class="timeline-date">Refund Complete</div>
                <div class="timeline-content">
                    <p>Service access immediately terminated</p>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">0-30 Days</div>
                <div class="timeline-content">
                    <p><strong>Data Retention Period</strong></p>
                    <p>Your account data (including NPC configurations, chat history, memories, etc.) will be retained on our servers for 30 days.</p>
                    <p>During this period, you may contact support@neshama.ai to restore your account.</p>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">After 30 Days</div>
                <div class="timeline-content">
                    <p><strong>Permanent Deletion</strong></p>
                    <p>All data will be permanently deleted and cannot be recovered.</p>
                </div>
            </div>
        </div>
        
        <h4>Data Recovery Options</h4>
        <p>If you change your mind and wish to continue using the service:</p>
        <ul>
            <li>Contact us within the 30-day retention period</li>
            <li>Resubscribe to the service</li>
            <li>Your data will be fully restored</li>
        </ul>
        
        <div class="refund-warning">
            <p><strong>Note:</strong> If you wish to permanently delete all data without recovery options, please clearly state "Permanently delete all data" in your refund request.</p>
        </div>`
    },
    'faq': {
        title: '6. Frequently Asked Questions',
        content: `<div class="refund-faq">
            <div class="faq-item">
                <h4>Q: Can I resubscribe after a refund?</h4>
                <p>A: Yes, you can resubscribe at any time. However, please note that resubscribing will be treated as a new subscription, not a renewal.</p>
            </div>
            
            <div class="faq-item">
                <h4>Q: How long does it take to receive my refund?</h4>
                <p>A: Generally, it takes 5-10 business days from request to receipt. The exact time depends on your bank or payment provider.</p>
            </div>
            
            <div class="faq-item">
                <h4>Q: If I used a free trial, can I still request a refund?</h4>
                <p>A: If you subscribed to a paid plan during the free trial period, the 14-day refund policy still applies.</p>
            </div>
            
            <div class="faq-item">
                <h4>Q: What happens to the NPCs I created after a refund?</h4>
                <p>A: Within the 30-day retention period, you can restore your account and continue using all NPCs. After 30 days, all NPC data will be permanently deleted.</p>
            </div>
            
            <div class="faq-item">
                <h4>Q: Can I file a complaint if I'm not satisfied with the service?</h4>
                <p>A: Absolutely. We value user feedback greatly. Please contact support@neshama.ai to explain your issue, and we will do our best to resolve it.</p>
            </div>
            
            <div class="faq-item">
                <h4>Q: Will Stripe processing fees be refunded?</h4>
                <p>A: The refund amount will be based on the actual subscription fee you paid. Stripe processing fees may not be included in the refund amount, depending on Stripe's policies.</p>
            </div>
        </div>`
    },
    'contact': {
        title: '7. Contact Us',
        content: `<p>If you have any questions about refunds, please contact us through the following methods:</p>
        
        <div class="contact-methods">
            <div class="contact-item">
                <h4>Refund Request Email</h4>
                <p><a href="mailto:support@neshama.ai">support@neshama.ai</a></p>
                <p class="contact-note">Please include "Refund Request" in the email subject line</p>
            </div>
            
            <div class="contact-item">
                <h4>Response Time</h4>
                <p>Business Hours: Monday to Friday, 9:00 AM - 6:00 PM (Beijing Time)</p>
                <p>We will respond to your email within 1-3 business days</p>
            </div>
            
            <div class="contact-item">
                <h4>Refund Inquiries</h4>
                <p>If you have submitted a refund request and haven't received your refund after 14 business days, please contact us with the following information:</p>
                <ul>
                    <li>Refund request date</li>
                    <li>Email used for the request</li>
                    <li>Refund reference number (if any)</li>
                </ul>
            </div>
        </div>
        
        <div class="refund-related-links">
            <h4>Related Links</h4>
            <ul>
                <li><a href="#" onclick="navigateTo('terms')">Terms of Service</a></li>
                <li><a href="#" onclick="navigateTo('privacy')">Privacy Policy</a></li>
                <li><a href="mailto:support@neshama.ai">Contact Support Team</a></li>
            </ul>
        </div>`
    }
};

// Navigation helper
function navigateTo(page) {
    if (typeof router !== 'undefined') {
        router.navigate(page);
    }
}

// Render Refund Policy Page
async function renderRefund() {
    const container = document.getElementById('page-refund');
    const isZh = getCurrentLang() === 'zh';
    const content = isZh ? refundContentZh : refundContentEn;
    const toc = REFUND_TOC;

    container.innerHTML = `
        <div class="legal-page refund-page">
            <div class="legal-header">
                <div class="legal-title-row">
                    <h1 class="legal-title">${isZh ? '退款政策' : 'Refund Policy'}</h1>
                    <div class="legal-lang-toggle">
                        <button class="lang-btn ${isZh ? 'active' : ''}" onclick="setLang('zh')">中文</button>
                        <button class="lang-btn ${!isZh ? 'active' : ''}" onclick="setLang('en')">EN</button>
                    </div>
                </div>
                <p class="legal-last-updated">
                    ${isZh ? '最后更新' : 'Last Updated'}: ${REFUND_LAST_UPDATED}
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
