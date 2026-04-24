# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_website_inquiry = fields.Boolean(
        string=_('Website Quote Request'),
        copy=False,
        help=_('Set when this quotation was submitted from the website quote request flow.'),
    )
    inquiry_contact_email = fields.Char(
        string=_('Inquiry Contact Email'),
        copy=False,
        help=_('Email address entered by the visitor when submitting the quote request.'),
    )
    inquiry_company_name = fields.Char(
        string=_('Inquiry Company Name'),
        copy=False,
        help=_('Optional company name submitted with the website quote request.'),
    )

    def _send_website_inquiry_notification(self, cfg):
        """Notify the configured administrator about a new website quote request.

        使用 ``force_send=False`` + ``mail.mail.send_after_commit()``：当前请求提交事务后再
        在新游标里发信，避免阻塞前台询价提交流程（SMTP 与部分投递逻辑在提交后执行）。
        """
        self.ensure_one()
        if not cfg or not (cfg.notify_email or '').strip():
            return
        template = self.env.ref(
            'website_sale_custom.mail_template_sale_order_website_inquiry',
            raise_if_not_found=False,
        )
        if not template:
            return
        # recipient_ids 清空：避免模板曾启用「默认收件人」时仍带上订单 partner（客户）
        email_values = {
            'email_to': (cfg.notify_email or '').strip(),
            'recipient_ids': [],
        }
        from_addr = (cfg.notify_email_from or '').strip()
        if from_addr:
            email_values['email_from'] = from_addr
        mail_id = template.with_user(SUPERUSER_ID).send_mail(
            self.id,
            force_send=False,
            raise_exception=False,
            email_values=email_values,
        )
        if mail_id:
            self.env['mail.mail'].sudo().browse(mail_id).send_after_commit()

    def _sync_inquiry_company_to_partner(self):
        """将询价单上的公司名称同步到客户（商业实体）。

        - 公司类型联系人：公司名称在 ``name`` 上；
        - 个人联系人：使用 ``company_name`` 文本字段。
        需在 ``partner_id``、``inquiry_company_name`` 已写入后调用（例如网站询价提交）。
        """
        self.ensure_one()
        company_name = (self.inquiry_company_name or '').strip()
        if not company_name or not self.partner_id:
            return
        partner = self.partner_id.commercial_partner_id.sudo()
        if partner.is_company:
            partner.write({'name': company_name})
        else:
            partner.write({'company_name': company_name})
