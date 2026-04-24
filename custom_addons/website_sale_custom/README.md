# Website Custom Sale (`website_sale_custom`)

面向 **Odoo 19** 的电商扩展：按 **网站** 配置结账/询价行为，提供前台 **Request a quote（询价）** 流程，并把结果落在 **销售订单** 上，同时支持管理员邮件通知。

---

## 依赖

- `website_sale`
- `mail`

---

## 安装与升级

1. 将 `addons_path` 包含本模块所在目录（如 `custom_addons`）。
2. 应用列表中安装或升级 **Website Custom Sale**。
3. 若修改了 `data/mail_template_data.xml` 且数据为 `noupdate="1"`，数据库里已存在的邮件模板可能不会自动覆盖；需在 **设置 → 技术 → 邮件 → 邮件模板** 中核对，或临时去掉 `noupdate` 后再升级。

---

## 后台配置

**路径**：`网站` → `电商` → `设置` → **Custom Sale Settings**（每个 **网站** 一条配置，`website_id` 唯一）。

| 字段 | 说明 |
|------|------|
| **Website** | 绑定的网站。 |
| **Enable Checkout** | 是否允许标准结账流程（购物车侧栏「下一步结账」、Express Checkout、付款步骤等）。关闭后仍可浏览商店，但结账相关入口由模板隐藏。 |
| **Enable Request Quote** | 是否启用前台 **Request a quote** 询价流程。 |
| **Show Checkout Steps on Cart** | 是否在 `/shop/cart` 顶部显示 **Order / Address / Payment** 步骤条。默认关；由 `Cart._cart_values` 注入 `show_wizard_checkout`。 |
| **Inquiry Notification Email** | 客户提交询价后，**仅**向该地址发送管理员通知邮件（`To`）。 |
| **Inquiry Notification From** | 通知邮件的 **发件人**（`email_from`）。模型上为必填；发送时仅当内容 **strip 后非空** 才写入 `email_from`，否则仍用邮件模板默认发件人。需与 SMTP 策略一致。 |

**权限**（`security/ir.model.access.csv`）：`website.group_website_designer`、`sales_team.group_sale_manager` 可读写 `website.custom.sale.config`。

---

## 前台功能概览

### 1. 结账开关（`website_sale.navigation_buttons` 继承）

- 根据 `custom_sale_enable_checkout` / `custom_sale_enable_inquiry` 控制购物车侧栏主按钮、付款块、Express Checkout、**Request a quote** 链接等。
- 注入变量来自 `website._get_checkout_step_values()`（内部合并 `_get_website_custom_sale_public_flags()`）。

### 2. 商品页询价入口（`website_sale.cta_wrapper` 继承）

- 在「加入购物车」旁显示 **Request a quote**（需开启询价）。
- 链接：`/shop/inquiry?product_id=<变体ID>&add_qty=1`，由控制器把该变体加入购物车后进入询价页。

### 3. 询价页 `/shop/inquiry`

- **GET**，需 `enable_inquiry`；无行则重定向购物车。
- 展示当前会话购物车订单行：数量、**期望单价**（默认 `_get_displayed_unit_price()`）、行备注。（前台 **Remove** 已暂时关闭：整表重载会丢未提交改价/数量；后端删除接口仍保留。）
- **整单备注** `inquiry_order_note`：提交后写入 `sale.order.note`（HTML，已转义换行）。
- 客户信息：邮箱（必填）、姓名（可选）、公司名（可选）。
- 前端脚本 `website_sale_inquiry_form.js`：按数量 × 期望单价更新行小计与合计（`data-currency-*`、`data-decimal-places`）。

### 4. 删除行 `POST /shop/inquiry/line/remove/<line_id>`（接口保留，前台按钮已关）

- CSRF；仅允许删除当前购物车订单中的行；删空后回购物车。
- 原询价页 **AJAX Remove** 在成功后请求 **`GET /shop/inquiry/table_fragment`** 替换整表，会导致用户未提交的改价/数量丢失，故 UI 已注释；需删行时请用户回购物车调整或后续再开放交互。

### 5. 提交询价 `POST /shop/inquiry/submit`

- 校验邮箱；按邮箱查找/创建 `res.partner`；更新行数量（≤0 则删行）；期望单价写入 **`sale.order.line.price_unit`**，行备注写入 **`inquiry_line_note`**。
- 订单：`is_website_inquiry`、`inquiry_contact_email`、`inquiry_company_name`；`_update_address` 绑定客户；**`_sync_inquiry_company_to_partner`** 把公司名同步到 `commercial_partner_id`（公司写 `name`，个人写 `company_name`）；再写 `note`；发邮件；**`sale_reset()`** 清空会话购物车；重定向感谢页。

### 6. 感谢页 `/shop/inquiry/done`

- 校验 `order_id` + `access_token` + `is_website_inquiry`。

---

## 数据模型

### `website.custom.sale.config`

每网站一条。字段见上表；当前模型中 **通知邮箱与发件人字段均为 `required=True`**，新建配置时需填写（发件人可填占位邮箱若业务上依赖模板默认 From，再视需求放宽模型约束）。

### `sale.order`（扩展）

| 字段 | 说明 |
|------|------|
| `is_website_inquiry` | 网站询价单标记。 |
| `inquiry_contact_email` | 访客提交的联系邮箱。 |
| `inquiry_company_name` | 访客填写的公司名（可选）。 |

**方法**：

- `_send_website_inquiry_notification(cfg)`：按配置发管理员邮件；`email_to` 仅配置地址；`recipient_ids: []` 防止默认带上客户；可选 `email_from`。使用 **`send_mail(..., force_send=False)` + `mail.mail.send_after_commit()`**，在数据库事务提交后再发信，减少阻塞前台提交。
- `_sync_inquiry_company_to_partner()`：询价公司名 → 客户商业实体。

### `sale.order.line`（扩展）

| 字段 | 说明 |
|------|------|
| `inquiry_line_note` | 询价行备注（前台 textarea）。 |

---

## 询价表单 POST 字段约定（与控制器一致）

| 用途 | 字段名 |
|------|--------|
| 联系邮箱 | `inquiry_email` |
| 联系人姓名 | `contact_name` |
| 公司名 | `inquiry_company_name` |
| 行数量 | `line_qty_<line_id>` |
| 期望单价 | `line_expected_<line_id>` |
| 行备注 | `line_note_<line_id>` |
| 整单备注 | `inquiry_order_note` |

---

## 邮件模板

- **XML ID**：`website_sale_custom.mail_template_sale_order_website_inquiry`
- **模型**：`sale.order`
- **`use_default_to`**：`False`，避免把订单 `partner_id`（客户）加入收件人。
- 正文中订单行 **单价** 使用 **`line.price_unit`**（与提交写入字段一致，勿使用不存在的 `inquiry_expected_price`）。
- 若存在 **`object.note`**（客户整单备注），在邮件中展示 **Order note** 区块。

发件逻辑见 `sale.order._send_website_inquiry_notification`：优先使用配置中的 **收件人 / 发件人**。

---

## 后台界面扩展

- **`sale.order` 表单**：网站询价信息分组（`is_website_inquiry`、`inquiry_contact_email`、`inquiry_company_name`）；订单行列表与表单中 **`inquiry_line_note`**（仅询价单显示）。

---

## 目录结构（便于维护）

```
website_sale_custom/
├── __init__.py
├── __manifest__.py
├── README.md                 # 本说明
├── controllers/
│   ├── __init__.py
│   ├── cart.py               # 购物车 show_wizard_checkout
│   └── inquiry.py            # 询价路由与提交逻辑
├── data/
│   └── mail_template_data.xml
├── models/
│   ├── __init__.py
│   ├── website_custom_sale_config.py
│   ├── website.py            # checkout 上下文 + 购物车 wizard 开关
│   ├── sale_order.py
│   └── sale_order_line.py
├── security/
│   └── ir.model.access.csv
├── static/src/js/
│   └── website_sale_inquiry_form.js
└── views/
    ├── website_custom_sale_config_views.xml
    ├── website_sale_inquiry_templates.xml
    └── sale_order_views.xml
```

---

## 已知注意点 / 后续可优化方向

1. **邮件模板与 `noupdate`**：生产库若长期 `noupdate="1"`，升级后请核对模板是否与仓库一致（字段名、默认收件人、正文区块）。
2. **`notify_email` / `notify_email_from` 与 help 文案**：`notify_email_from` 的 help 写「可留空」与当前 `required=True` 不一致；若希望真正可选，应去掉 `required` 或给默认值并在 `_send_website_inquiry_notification` 中保持「仅非空才写 `email_from`」。
3. **询价与结账并存**：逻辑由配置与 QWeb 控制；若需更严路由保护（例如关闭结账后禁止访问 `/shop/payment`），可在独立任务中加强。
4. **多语言**：前台文案当前多为英文；若要多语言可改为翻译词条或 `website` 翻译导出。
5. **安全与限流**：询价提交为公开路由，可按需加频率限制、验证码或蜜罐。

---

## 版本

以 `__manifest__.py` 中 **`version`** 为准（当前 `19.0.1.0.0`）。
