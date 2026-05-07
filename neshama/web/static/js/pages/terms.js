/**
 * Terms of Service Page - Service Terms and Conditions
 */

const TERMS_TOC = [
    { id: 'service-description', key: 'terms.toc.service' },
    { id: 'account-registration', key: 'terms.toc.account' },
    { id: 'acceptable-use', key: 'terms.toc.acceptableUse' },
    { id: 'intellectual-property', key: 'terms.toc.ip' },
    { id: 'pricing-payment', key: 'terms.toc.pricing' },
    { id: 'service-level', key: 'terms.toc.sla' },
    { id: 'data-backup', key: 'terms.toc.backup' },
    { id: 'termination', key: 'terms.toc.termination' },
    { id: 'disclaimer', key: 'terms.toc.disclaimer' },
    { id: 'limitation-liability', key: 'terms.toc.liability' },
    { id: 'dispute-resolution', key: 'terms.toc.dispute' },
    { id: 'terms-updates', key: 'terms.toc.updates' },
    { id: 'governing-law', key: 'terms.toc.law' },
    { id: 'contact-us', key: 'terms.toc.contact' }
];

const TERMS_LAST_UPDATED = '2026-03-01';

// Terms of Service Content - Chinese
const termsContentZh = {
    'service-description': {
        title: '一、服务描述',
        content: `<p><strong>Neshama NPC灵魂操作系统</strong>（以下简称"服务"）是由Neshama AI提供的在线平台，为用户提供创建、管理和与AI驱动的NPC（非玩家角色）进行交互的能力。</p>
        <p>服务包括但不限于：</p>
        <ul>
            <li>NPC人格配置系统（OCEAN人格模型）</li>
            <li>实时情绪模拟引擎</li>
            <li>多层记忆管理系统</li>
            <li>NPC对话生成API</li>
            <li>实体图谱可视化</li>
            <li>人格演化追踪</li>
        </ul>
        <p>我们保留随时修改、暂停或终止服务（或其任何部分）的权利，并不对用户承担此类变更的通知义务，除非法律另有要求。</p>`
    },
    'account-registration': {
        title: '二、账户注册与安全',
        content: `<p><strong>账户注册：</strong></p>
        <p>要使用我们的服务，您需要创建一个账户。注册时，您同意：</p>
        <ul>
            <li>提供准确、完整和最新的信息</li>
            <li>维护并及时更新您的账户信息</li>
            <li>对您的账户安全负责，包括保管好您的密码</li>
            <li>对账户下发生的所有活动承担责任</li>
        </ul>
        <p><strong>账户安全：</strong></p>
        <p>您同意立即通知我们任何未经授权使用您账户的情况。我们不对因您未能保护账户凭证而造成的任何损失负责。</p>
        <p><strong>账户资格：</strong></p>
        <p>您必须年满18岁或达到您所在司法管辖区的法定成年年龄才能创建账户并使用服务。</p>`
    },
    'acceptable-use': {
        title: '三、可接受使用政策',
        content: `<p>您同意不会使用服务从事以下活动：</p>
        <ul>
            <li><strong>违法内容：</strong>生成、传播或存储任何违法、有害、欺诈、骚扰、歧视、暴力或令人反感的内容</li>
            <li><strong>侵犯权利：</strong>侵犯任何第三方的知识产权、隐私权或其他合法权益</li>
            <li><strong>攻击NPC：</strong>利用服务攻击、骚扰或伤害其他用户的NPC</li>
            <li><strong>滥用API：</strong>过度使用、滥用或试图绕过我们的使用限制和速率限制</li>
            <li><strong>逆向工程：</strong>对服务进行反向工程、反编译或反汇编</li>
            <li><strong>未经授权访问：</strong>尝试未经授权访问我们的系统、网络或账户</li>
            <li><strong>干扰服务：</strong>干扰或破坏服务的正常运行</li>
            <li><strong>虚假信息：</strong>使用服务生成和传播虚假信息或 deepfake 内容</li>
        </ul>
        <p>违反此政策可能导致您的账户被暂停或终止，并可能承担法律责任。</p>`
    },
    'intellectual-property': {
        title: '四、知识产权',
        content: `<p><strong>Neshama的知识产权：</strong></p>
        <p>Neshama AI保留对本服务及其所有组件的全部知识产权，包括但不限于：</p>
        <ul>
            <li>服务代码、界面设计、算法</li>
            <li>Neshama的名称、标志和商标</li>
            <li>服务文档和营销材料</li>
        </ul>
        <p>您被授予使用服务的有限、非排他性、不可转让的许可，该许可在您遵守本条款的前提下有效。</p>
        <p><strong>您的知识产权：</strong></p>
        <p>您保留您在使用服务时创建的NPC人格配置、对话内容和自定义内容的知识产权。授予我们使用、存储和展示您创建内容以提供服务所需的权利。</p>
        <p><strong>反馈：</strong></p>
        <p>您向我们提供的任何反馈、建议或改进意见将被视为Neshama的财产，我们可以自由使用这些反馈而无需对您承担任何义务。</p>`
    },
    'pricing-payment': {
        title: '五、定价与付款',
        content: `<p><strong>订阅模式：</strong></p>
        <p>我们的服务采用月订阅模式。具体定价请参阅我们的定价页面。</p>
        <p><strong>自动续费：</strong></p>
        <p>您的订阅将在每个计费周期开始时自动续费，除非您在当前计费周期结束前取消订阅。取消后，您将继续拥有访问权限直到当前计费周期结束。</p>
        <p><strong>付款方式：</strong></p>
        <p>我们通过第三方支付处理器（Stripe）处理付款。我们不存储您的完整信用卡信息。付款将使用您选择的付款方式处理。</p>
        <p><strong>价格变动：</strong></p>
        <p>我们保留更改价格的权利。价格变动将在生效前至少30天通知您。价格变动不适用于当前计费周期。</p>
        <p><strong>退款政策：</strong></p>
        <p>有关详细信息，请参阅我们的退款政策页面。简而言之：</p>
        <ul>
            <li>首次订阅14天内可申请无理由全额退款</li>
            <li>超过14天按剩余天数比例退款</li>
            <li>额外购买的NPC包或交互包不支持退款</li>
        </ul>`
    },
    'service-level': {
        title: '六、服务级别',
        content: `<p><strong>可用性目标：</strong></p>
        <p>我们努力提供99.9%的正常运行时间，但这是一个目标而非保证。</p>
        <p><strong>维护窗口：</strong></p>
        <p>我们可能需要进行计划维护，期间服务可能不可用。我们将：</p>
        <ul>
            <li>尽可能提前通知您计划维护</li>
            <li>将维护安排在低流量时段进行</li>
        </ul>
        <p><strong>服务中断：</strong></p>
        <p>对于因以下原因造成的服务中断或数据丢失，我们不承担责任：</p>
        <ul>
            <li>我们无法控制的因素（如天灾、战争、恐怖主义等）</li>
            <li>第三方服务提供商的故障</li>
            <li>您的账户因违反本条款而被暂停</li>
            <li>紧急维护</li>
        </ul>
        <p><strong>服务 Credits：</strong></p>
        <p>如果月度正常运行时间低于99.9%，在符合条件的情况下，我们将根据服务水平协议提供服务 Credits。</p>`
    },
    'data-backup': {
        title: '七、数据备份',
        content: `<p><strong>用户责任：</strong></p>
        <p><strong>您有责任定期导出和备份您的重要数据。</strong>虽然我们会尽合理努力维护数据，但不对因数据丢失造成的任何损失负责。</p>
        <p><strong>备份功能：</strong></p>
        <p>我们提供服务的数据导出功能，允许您：</p>
        <ul>
            <li>导出NPC配置</li>
            <li>导出对话记录</li>
            <li>导出记忆数据</li>
        </ul>
        <p><strong>数据恢复：</strong></p>
        <p>在账户删除后30天内，您可以联系 support@neshama.ai 申请恢复您的数据。30天后，数据将被永久删除。</p>`
    },
    'termination': {
        title: '八、终止条款',
        content: `<p><strong>用户终止：</strong></p>
        <p>您可以随时通过以下方式终止您的账户：</p>
        <ul>
            <li>在账户设置中取消订阅</li>
            <li>联系 support@neshama.ai 请求账户删除</li>
        </ul>
        <p>终止后，您的账户将进入30天宽限期，期间数据仍可恢复。</p>
        <p><strong>Neshama终止：</strong></p>
        <p>如果我们认为您违反了本服务条款，我们可能：</p>
        <ul>
            <li>警告您</li>
            <li>暂停您的账户或访问权限</li>
            <li>立即终止您的账户</li>
        </ul>
        <p><strong>终止后的义务：</strong></p>
        <p>账户终止后：</p>
        <ul>
            <li>您将无法再访问您的账户和服务</li>
            <li>您仍然对终止前产生的任何费用负责</li>
            <li>我们将在30天后永久删除您的数据（除非法律要求保留更长时间）</li>
        </ul>`
    },
    'disclaimer': {
        title: '九、免责声明',
        content: `<p><strong>服务按"现状"提供：</strong></p>
        <p>NESHAMA AI 明确声明不对服务作出任何明示或暗示的保证，包括但不限于：</p>
        <ul>
            <li>服务的适销性、特定用途适用性</li>
            <li>服务不会中断、安全、及时或无错误</li>
            <li>通过服务获得的结果的准确性或可靠性</li>
            <li>任何内容、信息或服务的质量</li>
        </ul>
        <p><strong>NPC对话内容：</strong></p>
        <p><strong>通过服务生成的NPC对话内容由人工智能模型自动创建，不代表Neshama的观点、立场或价值观。</strong>我们不对NPC生成的任何内容负责。您使用NPC对话内容的风险由您自行承担。</p>
        <p><strong>第三方内容：</strong></p>
        <p>服务可能包含指向第三方网站或内容的链接。我们不对第三方内容、服务或网站负责。</p>`
    },
    'limitation-liability': {
        title: '十、责任限制',
        content: `<p><strong>责任上限：</strong></p>
        <p>在适用法律允许的最大范围内，<strong>我们对您的全部责任（无论出于合同、侵权或其他原因）不得超过您在索赔发生前12个月内实际支付给我们的金额。</strong></p>
        <p><strong>间接损害排除：</strong></p>
        <p>在适用法律允许的最大范围内，NESHAMA AI 不对以下损害承担责任：</p>
        <ul>
            <li>间接、特殊、偶然、惩罚性或后果性损害</li>
            <li>利润损失、收入损失、商誉损失、数据丢失</li>
            <li>替代服务或商品的成本</li>
            <li>任何超出我们合理控制的事项</li>
        </ul>
        <p><strong>例外：</strong></p>
        <p>上述限制不适用于：</p>
        <ul>
            <li>我们故意不当行为或欺诈</li>
            <li>造成人身伤害（死亡除外）</li>
            <li>适用法律禁止的情形</li>
        </ul>`
    },
    'dispute-resolution': {
        title: '十一、争议解决',
        content: `<p><strong>仲裁协议：</strong></p>
        <p>您和 Neshama AI 同意，任何因本服务条款或服务引起的或与之相关的争议、索赔或纠纷，将通过有约束力的仲裁解决，而不是通过法院诉讼。</p>
        <p><strong>仲裁程序：</strong></p>
        <ul>
            <li>仲裁将由中立的仲裁员进行</li>
            <li>仲裁将在您注册的账户地址所在地或双方约定的地点进行</li>
            <li>仲裁过程和裁决将被保密</li>
        </ul>
        <p><strong>例外 - 小额索赔：</strong></p>
        <p>尽管有上述仲裁协议，如果您的争议符合小额索赔法院的条件，您可以在小额索赔法院提起诉讼。</p>
        <p><strong>集体诉讼放弃：</strong></p>
        <p>您和 Neshama AI 同意放弃作为原告或集体成员参与任何集体诉讼或代表诉讼的权利。</p>`
    },
    'terms-updates': {
        title: '十二、条款更新',
        content: `<p><strong>更新通知：</strong></p>
        <p>我们可能会不时更新本服务条款。更新时：</p>
        <ul>
            <li>我们将在生效日期前至少30天通过电子邮件通知您</li>
            <li>重大变更将在我们的网站上发布</li>
            <li>条款顶部将显示新的"最后更新"日期</li>
        </ul>
        <p><strong>接受更新：</strong></p>
        <p>在更新生效后，如果您继续使用服务，即表示您接受更新后的条款。</p>
        <p><strong>不同意条款：</strong></p>
        <p>如果您不同意更新后的条款，您应：</p>
        <ul>
            <li>在更改生效前停止使用服务</li>
            <li>取消您的订阅并删除您的账户</li>
        </ul>`
    },
    'governing-law': {
        title: '十三、适用法律',
        content: `<p>本服务条款的解释、执行和效力应受美国特拉华州法律的管辖，但不影响任何法律冲突原则。</p>
        <p>如果您是欧盟用户，本条款不影响您在当地法律下享有的权利，包括 GDPR 下的权利。</p>
        <p>如果您是加州用户，CCPA 赋予您的权利不受本条款的影响。</p>`
    },
    'contact-us': {
        title: '十四、联系我们',
        content: `<p>如果您对本服务条款有任何疑问，请通过以下方式联系我们：</p>
        <ul>
            <li><strong>法律相关：</strong>legal@neshama.ai</li>
            <li><strong>一般支持：</strong>support@neshama.ai</li>
            <li><strong>退款请求：</strong>support@neshama.ai</li>
        </ul>
        <p><strong>实体名称：</strong>Neshama AI</p>
        <p><strong>注册地址：</strong>特拉华州，美国</p>`
    }
};

// Terms of Service Content - English
const termsContentEn = {
    'service-description': {
        title: '1. Service Description',
        content: `<p><strong>Neshama NPC Soul Operating System</strong> (the "Service") is an online platform provided by Neshama AI that enables users to create, manage, and interact with AI-driven NPCs (Non-Player Characters).</p>
        <p>The Service includes, but is not limited to:</p>
        <ul>
            <li>NPC personality configuration system (OCEAN personality model)</li>
            <li>Real-time emotion simulation engine</li>
            <li>Multi-layer memory management system</li>
            <li>NPC conversation generation API</li>
            <li>Entity graph visualization</li>
            <li>Personality evolution tracking</li>
        </ul>
        <p>We reserve the right to modify, suspend, or discontinue the Service (or any part thereof) at any time without obligation to notify users, except as required by law.</p>`
    },
    'account-registration': {
        title: '2. Account Registration and Security',
        content: `<p><strong>Account Registration:</strong></p>
        <p>To use our Service, you must create an account. When registering, you agree to:</p>
        <ul>
            <li>Provide accurate, complete, and current information</li>
            <li>Maintain and promptly update your account information</li>
            <li>Take responsibility for the security of your account, including keeping your password safe</li>
            <li>Accept responsibility for all activities under your account</li>
        </ul>
        <p><strong>Account Security:</strong></p>
        <p>You agree to notify us immediately of any unauthorized use of your account. We are not liable for any loss arising from your failure to protect your account credentials.</p>
        <p><strong>Account Eligibility:</strong></p>
        <p>You must be at least 18 years old or have reached the age of majority in your jurisdiction to create an account and use the Service.</p>`
    },
    'acceptable-use': {
        title: '3. Acceptable Use Policy',
        content: `<p>You agree not to use the Service to engage in the following activities:</p>
        <ul>
            <li><strong>Illegal Content:</strong> Generate, distribute, or store any illegal, harmful, fraudulent, harassing, discriminatory, violent, or objectionable content</li>
            <li><strong>Rights Violation:</strong> Infringe any third party's intellectual property rights, privacy rights, or other legal rights</li>
            <li><strong>NPC Attacks:</strong> Use the Service to attack, harass, or harm other users' NPCs</li>
            <li><strong>API Abuse:</strong> Overuse, abuse, or attempt to circumvent our usage limits and rate limits</li>
            <li><strong>Reverse Engineering:</strong> Reverse engineer, decompile, or disassemble the Service</li>
            <li><strong>Unauthorized Access:</strong> Attempt unauthorized access to our systems, networks, or accounts</li>
            <li><strong>Service Interference:</strong> Interfere with or disrupt the proper functioning of the Service</li>
            <li><strong>Misinformation:</strong> Use the Service to generate and distribute false information or deepfake content</li>
        </ul>
        <p>Violations of this policy may result in suspension or termination of your account and may expose you to legal liability.</p>`
    },
    'intellectual-property': {
        title: '4. Intellectual Property',
        content: `<p><strong>Neshama's Intellectual Property:</strong></p>
        <p>Neshama AI retains all intellectual property rights in and to the Service and all its components, including but not limited to:</p>
        <ul>
            <li>Service code, interface design, algorithms</li>
            <li>Neshama's name, logo, and trademarks</li>
            <li>Service documentation and marketing materials</li>
        </ul>
        <p>You are granted a limited, non-exclusive, non-transferable license to use the Service, effective as long as you comply with these Terms.</p>
        <p><strong>Your Intellectual Property:</strong></p>
        <p>You retain intellectual property rights in the NPC personality configurations, conversation content, and custom content you create using the Service. You grant us the rights to use, store, and display your created content as necessary to provide the Service.</p>
        <p><strong>Feedback:</strong></p>
        <p>Any feedback, suggestions, or improvement ideas you provide to us will be considered the property of Neshama, and we may use such feedback freely without obligation to you.</p>`
    },
    'pricing-payment': {
        title: '5. Pricing and Payment',
        content: `<p><strong>Subscription Model:</strong></p>
        <p>Our Service is offered on a monthly subscription basis. See our pricing page for current pricing details.</p>
        <p><strong>Automatic Renewal:</strong></p>
        <p>Your subscription will automatically renew at the beginning of each billing cycle unless you cancel your subscription before the end of the current billing cycle. After cancellation, you will continue to have access until the end of the current billing cycle.</p>
        <p><strong>Payment Methods:</strong></p>
        <p>We process payments through a third-party payment processor (Stripe). We do not store your complete credit card information. Payments will be processed using your selected payment method.</p>
        <p><strong>Price Changes:</strong></p>
        <p>We reserve the right to change prices. Price changes will be notified at least 30 days before they take effect. Price changes will not apply to the current billing cycle.</p>
        <p><strong>Refund Policy:</strong></p>
        <p>See our Refund Policy page for details. In brief:</p>
        <ul>
            <li>Full refund within 14 days of first subscription (no reason required)</li>
            <li>After 14 days, prorated refund based on remaining days</li>
            <li>Additional NPC packs or interaction packs are non-refundable</li>
        </ul>`
    },
    'service-level': {
        title: '6. Service Level',
        content: `<p><strong>Availability Target:</strong></p>
        <p>We strive to achieve 99.9% uptime, but this is a target and not a guarantee.</p>
        <p><strong>Maintenance Windows:</strong></p>
        <p>We may need to perform scheduled maintenance during which the Service may be unavailable. We will:</p>
        <ul>
            <li>Notify you in advance whenever possible</li>
            <li>Schedule maintenance during low-traffic periods</li>
        </ul>
        <p><strong>Service Interruptions:</strong></p>
        <p>We are not liable for any service interruptions or data loss caused by:</p>
        <ul>
            <li>Factors beyond our control (such as natural disasters, war, terrorism, etc.)</li>
            <li>Third-party service provider failures</li>
            <li>Your account being suspended for violations of these Terms</li>
            <li>Emergency maintenance</li>
        </ul>
        <p><strong>Service Credits:</strong></p>
        <p>If monthly uptime falls below 99.9%, we will provide Service Credits as specified in the Service Level Agreement when eligible.</p>`
    },
    'data-backup': {
        title: '7. Data Backup',
        content: `<p><strong>User Responsibility:</strong></p>
        <p><strong>You are responsible for regularly exporting and backing up your important data.</strong> While we make reasonable efforts to maintain data, we are not liable for any loss resulting from data loss.</p>
        <p><strong>Backup Functionality:</strong></p>
        <p>We provide data export functionality allowing you to:</p>
        <ul>
            <li>Export NPC configurations</li>
            <li>Export conversation history</li>
            <li>Export memory data</li>
        </ul>
        <p><strong>Data Recovery:</strong></p>
        <p>Within 30 days after account deletion, you may contact support@neshama.ai to request data recovery. After 30 days, data will be permanently deleted.</p>`
    },
    'termination': {
        title: '8. Termination',
        content: `<p><strong>Termination by User:</strong></p>
        <p>You may terminate your account at any time by:</p>
        <ul>
            <li>Canceling your subscription in account settings</li>
            <li>Contacting support@neshama.ai to request account deletion</li>
        </ul>
        <p>After termination, your account will enter a 30-day grace period during which data can be recovered.</p>
        <p><strong>Termination by Neshama:</strong></p>
        <p>If we believe you have violated these Terms of Service, we may:</p>
        <ul>
            <li>Warn you</li>
            <li>Suspend your account or access</li>
            <li>Immediately terminate your account</li>
        </ul>
        <p><strong>Obligations After Termination:</strong></p>
        <p>After account termination:</p>
        <ul>
            <li>You will no longer be able to access your account and the Service</li>
            <li>You remain liable for any charges incurred before termination</li>
            <li>We will permanently delete your data after 30 days (unless required by law to retain longer)</li>
        </ul>`
    },
    'disclaimer': {
        title: '9. Disclaimer',
        content: `<p><strong>Service Provided "As Is":</strong></p>
        <p>NESHAMA AI EXPRESSLY DISCLAIMS ALL WARRANTIES, WHETHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:</p>
        <ul>
            <li>Merchantability, fitness for a particular purpose</li>
            <li>That the Service will be uninterrupted, secure, timely, or error-free</li>
            <li>Accuracy or reliability of results obtained from the Service</li>
            <li>Quality of any content, information, or service</li>
        </ul>
        <p><strong>NPC Conversation Content:</strong></p>
        <p><strong>NPC conversation content generated through the Service is automatically created by AI models and does not represent Neshama's views, positions, or values.</strong> We are not responsible for any content generated by NPCs. You use NPC conversation content at your own risk.</p>
        <p><strong>Third-Party Content:</strong></p>
        <p>The Service may contain links to third-party websites or content. We are not responsible for third-party content, services, or websites.</p>`
    },
    'limitation-liability': {
        title: '10. Limitation of Liability',
        content: `<p><strong>Liability Cap:</strong></p>
        <p>To the maximum extent permitted by applicable law, <strong>our total liability to you for any claims (whether in contract, tort, or otherwise) shall not exceed the amount you actually paid us in the 12 months preceding the claim.</strong></p>
        <p><strong>Exclusion of Indirect Damages:</strong></p>
        <p>To the maximum extent permitted by applicable law, NESHAMA AI SHALL NOT BE LIABLE FOR:</p>
        <ul>
            <li>Indirect, special, incidental, punitive, or consequential damages</li>
            <li>Loss of profits, revenue, goodwill, or data</li>
            <li>Cost of substitute services or goods</li>
            <li>Any matter beyond our reasonable control</li>
        </ul>
        <p><strong>Exceptions:</strong></p>
        <p>The above limitations do not apply to:</p>
        <ul>
            <li>Our intentional misconduct or fraud</li>
            <li>Personal injury (except death)</li>
            <li>Where prohibited by applicable law</li>
        </ul>`
    },
    'dispute-resolution': {
        title: '11. Dispute Resolution',
        content: `<p><strong>Arbitration Agreement:</strong></p>
        <p>You and Neshama AI agree that any dispute, claim, or controversy arising out of or relating to these Terms of Service or the Service shall be resolved through binding arbitration rather than court litigation.</p>
        <p><strong>Arbitration Process:</strong></p>
        <ul>
            <li>Arbitration will be conducted by a neutral arbitrator</li>
            <li>Arbitration will take place in the state of your registered account address or another mutually agreed location</li>
            <li>Arbitration proceedings and awards will be kept confidential</li>
        </ul>
        <p><strong>Exception - Small Claims:</strong></p>
        <p>Notwithstanding the above arbitration agreement, if your dispute qualifies for small claims court, you may file suit in small claims court.</p>
        <p><strong>Class Action Waiver:</strong></p>
        <p>You and Neshama AI agree to waive the right to participate as a plaintiff or class member in any class action or representative proceeding.</p>`
    },
    'terms-updates': {
        title: '12. Terms Updates',
        content: `<p><strong>Update Notification:</strong></p>
        <p>We may update these Terms of Service from time to time. When updating:</p>
        <ul>
            <li>We will notify you via email at least 30 days before the changes take effect</li>
            <li>Significant changes will be posted on our website</li>
            <li>The new "Last Updated" date will be shown at the top of the Terms</li>
        </ul>
        <p><strong>Accepting Updates:</strong></p>
        <p>By continuing to use the Service after updates take effect, you accept the updated Terms.</p>
        <p><strong>Disagreeing with Terms:</strong></p>
        <p>If you disagree with the updated Terms, you should:</p>
        <ul>
            <li>Stop using the Service before the changes take effect</li>
            <li>Cancel your subscription and delete your account</li>
        </ul>`
    },
    'governing-law': {
        title: '13. Governing Law',
        content: `<p>The interpretation, enforcement, and validity of these Terms of Service shall be governed by the laws of the State of Delaware, USA, without regard to conflict of law principles.</p>
        <p>If you are an EU user, these Terms do not affect your rights under local law, including rights under GDPR.</p>
        <p>If you are a California user, your rights under CCPA are not affected by these Terms.</p>`
    },
    'contact-us': {
        title: '14. Contact Us',
        content: `<p>If you have any questions about these Terms of Service, please contact us:</p>
        <ul>
            <li><strong>Legal Matters:</strong> legal@neshama.ai</li>
            <li><strong>General Support:</strong> support@neshama.ai</li>
            <li><strong>Refund Requests:</strong> support@neshama.ai</li>
        </ul>
        <p><strong>Entity Name:</strong> Neshama AI</p>
        <p><strong>Registered Address:</strong> Delaware, USA</p>`
    }
};

// Render Terms of Service Page
async function renderTerms() {
    const container = document.getElementById('page-terms');
    const isZh = getCurrentLang() === 'zh';
    const content = isZh ? termsContentZh : termsContentEn;
    const toc = TERMS_TOC;

    container.innerHTML = `
        <div class="legal-page">
            <div class="legal-header">
                <div class="legal-title-row">
                    <h1 class="legal-title">${isZh ? '服务条款' : 'Terms of Service'}</h1>
                    <div class="legal-lang-toggle">
                        <button class="lang-btn ${isZh ? 'active' : ''}" onclick="setLang('zh')">中文</button>
                        <button class="lang-btn ${!isZh ? 'active' : ''}" onclick="setLang('en')">EN</button>
                    </div>
                </div>
                <p class="legal-last-updated">
                    ${isZh ? '最后更新' : 'Last Updated'}: ${TERMS_LAST_UPDATED}
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
