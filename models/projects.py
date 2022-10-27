from datetime import date, datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class farm_projects(models.Model):
    _name = 'farm.projects'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Farm Projects Management'
    _check_company_auto = True
    _sql_constraints = [
        ('short_name_uniq', 'unique(short_name)', "A short name can only be assigned to one project !"),
    ]

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string = "Priority",
        help = 'Set the project priority which view first')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_operation', 'In Operation'),
        ('finish', 'Finished'),
        ('on_hold', 'On hold')],
        string = 'Status',
        group_expand = '_group_expand_states',
        readonly = False,
        required = True,
        tracking = True,
        copy = False,
        default = 'draft',
        help = "Set whether the project process is open or closed to start or end operations.")
    name = fields.Char(
        string = 'Project Ref',
        index = True,
        tracking = True,
        default = lambda x: _('New'))
    short_name = fields.Char(
        string = 'Project Name',
        required = True,
        help = "Enter a short name",
        translate = True,
        tracking = True)
    project_type = fields.Selection([
        ('create', 'Produce a Pio-Asset or Crop'),  # produce only, product must be storable
        ('operate', 'Produce and Sell'),  # produce and sell , product must be storable
        ('sale', 'Sell directly product  as consumable'),  # product must be consumable
        ('service', 'Service of an Asset or a Function'),
        # product must be service and the bills will be collected as invoices
    ],
        required = True,
        help = "Select the type Produce, Sell or Both, either Service",
        string = 'Type',
        default = 'operate',
        tracking = True)
    project_group_id = fields.Many2one(
        comodel_name = 'farm.project.group',
        string = 'Project Group',
        required = True)
    user_id = fields.Many2one(
        comodel_name = 'res.users',
        string = "Project Man",
        required = True)
    description = fields.Text(
        string = 'Description',
        required = False,
        help = "Enter the description",
        translate = True,
        tracking = True)
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)
    start_date = fields.Date(
        string = 'Start Date',
        required = True,
        tracking = True,
        default = datetime.today())
    end_date = fields.Date(
        string = 'End Date',
        required = True,
        store = True,
        compute = '_get_end_date',
        inverse = '_set_end_date')
    close_date = fields.Date(
        string = 'Close Date',
        tracking = True,
        store = True,
        inverse = '_get_actual_gone')
    p_days = fields.Integer(
        string = 'Plan Days',
        store = True)
    g_days = fields.Integer(
        string = 'Days Gone',
        store = True,
        readonly = True)
    a_days = fields.Integer(
        string = 'Actual Days',
        store = True,
        readonly = True,
        compute = '_get_time_gone')
    operation_budget = fields.Monetary(
        string = 'Operation Budget',
        compute = '_compute_operation_budget',
        currency_field = 'currency_id',
        required = False,
        tracking = True)
    material_budget = fields.Monetary(
        string = 'Material Budget',
        compute = '_compute_material_budget',
        currency_field = 'currency_id',
        required = False,
        tracking = True)
    expense_budget = fields.Monetary(
        string = 'Expense Budget',
        compute = '_compute_expense_budget',
        currency_field = 'currency_id',
        required = False,
        tracking = True)
    plan_produce_qty = fields.Float(
        string = 'Produce Plan Qty',
        required = False,
        readonly = True,
        tracking = True)
    plan_produce_amount = fields.Monetary(
        string = 'Produce Budget',
        compute = '_compute_plan_produce_amount',
        currency_field = 'currency_id',
        required = False,
        readonly = True,
        tracking = True)
    plan_sales_qty = fields.Float(
        string = 'Sales Plan Qty',
        required = False,
        readonly = True,
        tracking = True)
    plan_sales_amount = fields.Monetary(
        string = 'Sales Budget',
        compute = '_compute_plan_sales_amount',
        currency_field = 'currency_id',
        readonly = True,
        required = False,
        tracking = True)
    operations_actual = fields.Monetary(
        string = 'Operation Actual',
        compute = '_compute_operations_actual',
        currency_field = 'currency_id',
        required = False,
        tracking = True)
    materials_actual = fields.Monetary(
        string = 'Material Actual',
        compute = '_compute_materials_actual',
        currency_field = 'currency_id',
        required = False,
        tracking = True)
    expenses_actual = fields.Monetary(
        string = 'Expense Actual',
        compute = '_compute_expenses_actual',
        currency_field = 'currency_id',
        required = False,
        tracking = True)
    actual_produce_qty = fields.Float(
        string = 'Produce Act. Qty',
        compute = '_compute_sum_produce_qty',
        required = False,
        readonly = True)
    actual_produce_amount = fields.Monetary(
        string = 'Produce Act. Amount',
        compute = '_compute_actual_produce_amount',
        currency_field = 'currency_id',
        required = False,
        readonly = True)
    actual_sales_qty = fields.Float(
        string = 'Sales Act. Qty',
        required = False,
        readonly = True)
    actual_sales_amount = fields.Monetary(
        string = 'Sales Act. Amount',
        compute = '_compute_actual_sales_amount',
        currency_field = 'currency_id',
        required = False,
        readonly = True)
    operations_id = fields.Many2one(
        comodel_name = 'farm.operations',
        string = "Project Operations")
    operations_ids = fields.One2many(
        comodel_name = 'farm.operations',
        inverse_name = 'projects_id',
        string = "Operation Orders")
    operations_count = fields.Integer(
        string = "Operation Count",
        compute = '_compute_operations_count')
    materials_id = fields.Many2one(
        comodel_name = 'farm.materials',
        string = "Project Materials")
    materials_ids = fields.One2many(
        comodel_name = 'farm.materials',
        inverse_name = 'projects_id',
        string = "Material Orders")
    materials_count = fields.Integer(
        string = "Material Count",
        compute = '_compute_materials_count')
    expenses_id = fields.Many2one(
        comodel_name = 'farm.expenses',
        string = "Project Expenses")
    expenses_ids = fields.One2many(
        comodel_name = 'farm.expenses',
        inverse_name = 'projects_id',
        string = "Expenses Orders")
    expenses_count = fields.Integer(
        string = "Expense Count",
        compute = '_compute_expenses_count')
    produce_id = fields.Many2one(
        comodel_name = 'farm.produce',
        string = "Produce Orders")
    produce_ids = fields.One2many(
        comodel_name = 'farm.produce',
        inverse_name = 'projects_id',
        string = "Produce Orders")
    produce_count = fields.Integer(
        string = "Produce Count",
        compute = '_compute_produce_count')
    sales_id = fields.Many2one(
        comodel_name = 'farm.sales',
        string = "Sales Orders")
    sales_ids = fields.One2many(
        comodel_name = 'farm.sales',
        inverse_name = 'projects_id',
        string = "Sales Orders")
    sales_count = fields.Integer(
        string = "Sales Count",
        compute = '_compute_sales_count')
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        index = True,
        required = True,
        change_default = True,
        readonly = True,
        default = lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name = 'res.currency',
        string = 'Currency',
        related = 'company_id.currency_id',
        readonly = True,
        ondelete = 'set null',
        help = "Used to display the currency when tracking monetary values")
    locations_used_ids = fields.One2many(
        comodel_name = 'farm.location.used',
        inverse_name = 'projects_id',
        string = "locations Used")
    # set of Key performance indicators
    time_progress = fields.Integer(
        string = 'Time Gone',
        compute = '_compute_time_progress')
    total_budget = fields.Float(
        string = 'Order Budget',
        compute = '_compute_total_budget')
    total_actual = fields.Float(
        string = 'Actual Spend',
        compute = '_compute_total_actual')
    total_actual04 = fields.Float(
        related = 'total_actual',
        string = 'Actual Spend vs Budget')
    total_actual05 = fields.Float(
        related = 'total_actual',
        string = 'Actual Spend vs Executed Order')
    total_actual06 = fields.Float(
        related = 'total_actual',
        string = 'Actual Spend vs Sales')
    cost_progress = fields.Integer(
        string = 'Expenses Actual vs Budget',
        compute = '_compute_cost_progress')
    total_actual_service = fields.Float(
        string = 'Total Service Plan',
        help = 'Total of Service internal bills plus external invoices.',
        compute = '_compute_total_actual_service')
    service_progress = fields.Integer(
        string = 'Expenses Actual vs Plan',
        help = 'compute % of actual spent vs actual bills and invoices',
        compute = '_compute_service_progress')
    average_produce_price = fields.Float(
        string = 'Average Produce Price',
        help = 'compute average price of stock move',
        compute = '_compute_average_produce_price'
    )
    average_sales_price = fields.Float(
        string = 'Average Sales Price',
        help = 'compute average price of sales invoices',
        compute = '_compute_average_sales_price'
    )
    cog_produce_price = fields.Float(
        string = 'Cost of Goods Produce Price',
        help = 'compute price of cost of goods produce based on actual produce qty and current actual spending',
        compute = '_compute_cog_produce_price'
    )
    # actual spend divided by sales volume
    cog_sales_price = fields.Float(
        string = 'Cost of Goods Sold Price',
        help = 'compute price of cost of goods sold based on actual sold qty and current actual spending',
        compute = '_compute_cog_sales_price')

    category_id = fields.Many2one(
        comodel_name = 'product.category',
        required = True,
        default = lambda self: self.env.ref('ms_farm.product_category_produce'),
        string = 'Product Category')
    buy_sell_price = fields.Float(
        string = 'buy  and sell price',
        store = True)
    analytic_account_id = fields.Reference(
        selection = [
            ('account.analytic.account', 'Analytic Account')
        ],
        string = 'Analytic Account')
    create_lock = fields.Boolean(
        string = 'Create Lock',
        default = False)
    product_id = fields.Many2one(
        comodel_name = 'product.product',
        string = "Relative Product")
    order_ids = fields.One2many(
        comodel_name = 'farm.operations.oline',
        inverse_name = 'product_id',
        string = "Operation Order Lines",
        compute = '_operations_order_lines')
    bills_ids = fields.One2many(
        comodel_name = 'account.move.line',
        inverse_name = 'product_id',
        string = "Bill Lines",
        compute = '_bills_order_lines')

    @api.depends('product_id')
    def _operations_order_lines(self):
        for rec in self:
            ope_line = self.env['farm.operations.oline'].search([
                ('product_id', '=', rec.product_id.id)
            ])
            rec.order_ids = ope_line
        return rec.order_ids

    @api.depends('product_id')
    def _bills_order_lines(self):
        for rec in self:
            ope_line = self.env['account.move.line'].search([
                ('product_id', '=', rec.product_id.id),
                ('move_type', '=', 'in_invoice'),
            ])
            rec.bills_ids = ope_line
        return rec.bills_ids

    @api.depends('state')
    def button_draft(self):
        for rec in self:
            rec.state = 'draft'

    def button_in_operation(self):
        for rec in self:
            rec.state = 'in_operation'

    def button_finish(self):
        for rec in self:
            rec.state = 'finish'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Congratulation!',
                'type': 'rainbow_man',
            }
        }

    def button_on_hold(self):
        for rec in self:
            rec.state = 'on_hold'

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('start_date', 'close_date')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.p_days):
                r.end_date = r.start_date
                continue
            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            p_days = timedelta(days = r.p_days, seconds = 0)
            r.end_date = r.start_date + p_days
        return r.end_date

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                raise UserError(_('Please define start and End date for current project for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.p_days = (r.end_date - r.start_date).days
        return r.p_days

    @api.depends('end_date')
    def _get_time_gone(self):
        self.ensure_one()
        if not self.end_date:
            self.g_days = 0
        elif not self.start_date:
            raise UserError(_('Please define start date for current project for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        else:
            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            self.g_days = (date.today() - self.start_date).days + 1
        return self.g_days

    def _get_actual_gone(self):
        self.ensure_one()
        if not self.close_date:
            self.a_days = 0
        else:
            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            self.a_days = (self.close_date - self.start_date).days
        return self.a_days

    @api.model
    def _compute_time_progress(self):
        for r in self:
            if not r.start_date:
                r.time_progress = 0
                continue
            # Compute integer of time gone vs planned days
            r.time_progress = abs(r.g_days / r.p_days * 100)
        return r.time_progress

    @api.model
    def _compute_total_budget(self):
        for r in self:
            # Compute the percent based on major cost till add expense module,
            r.total_budget = (r.operation_budget + r.material_budget + r.expense_budget)
        return r.total_budget

    @api.model
    def _compute_total_actual(self):
        for r in self:
            # Compute the percent based on major cost till add expense module,
            r.total_actual = (r.operations_actual + r.materials_actual + r.expenses_actual)
        return r.total_actual

    @api.model
    def _compute_cost_progress(self):
        for r in self:
            if not r.total_budget:
                r.cost_progress = 0
                continue
            # Compute the percent based on major cost till add expense module,
            r.cost_progress = abs(r.total_actual / r.total_budget * 100)
        return r.cost_progress

    @api.model
    def _compute_service_progress(self):
        for r in self:
            if not r.total_actual_service:
                r.service_progress = 0
                continue
            # Compute the percent based on major cost till add expense module,
            r.service_progress = abs(r.total_actual / r.total_actual_service * 100)
        return r.service_progress

    # compute amount of operation orders plus sales
    @api.model
    def _compute_total_actual_service(self):
        for r in self:
            if not r.product_id:
                print('need a product')
            else:
                bills_amount_debit = sum(
                    self.env['account.move.line'].search([
                        ('product_id', '=', r.product_id.id),
                        ('move_type', '=', 'in_invoice'),
                    ]).mapped('debit')
                )
                bills_amount_credit = sum(
                    self.env['account.move.line'].search([
                        ('product_id', '=', r.product_id.id),
                        ('move_type', '=', 'in_invoice'),
                    ]).mapped('credit')
                )

                invoice_amount_debit = sum(
                    self.env['account.move.line'].search([
                        ('product_id', '=', r.product_id.id),
                        ('move_type', '=', 'out_invoice'),
                    ]).mapped('debit')
                )
                invoice_amount_credit = sum(
                    self.env['account.move.line'].search([
                        ('product_id', '=', r.product_id.id),
                        ('move_type', '=', 'out_invoice'),
                    ]).mapped('credit')
                )
                r.total_actual_service = (
                        bills_amount_debit - bills_amount_credit + invoice_amount_credit - invoice_amount_debit)
        return r.total_actual_service

    def _compute_operations_count(self):
        for rec in self:
            operations_count = self.env['farm.operations'].search_count([
                ('projects_id', '=', rec.id)
            ])
            rec.operations_count = operations_count

    def _compute_materials_count(self):
        for rec in self:
            materials_count = self.env['farm.materials'].search_count([
                ('projects_id', '=', rec.id)
            ])
            rec.materials_count = materials_count

    def _compute_expenses_count(self):
        for rec in self:
            expenses_count = self.env['farm.expenses'].search_count([
                ('projects_id', '=', rec.id)
            ])
            rec.expenses_count = expenses_count

    def _compute_produce_count(self):
        for rec in self:
            produce_count = self.env['farm.produce'].search_count([
                ('projects_id', '=', rec.id)
            ])
            rec.produce_count = produce_count

    def _compute_sales_count(self):
        for rec in self:
            sales_count = self.env['farm.sales'].search_count([
                ('projects_id', '=', rec.id)
            ])
            rec.sales_count = sales_count

    def _compute_operation_budget(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.operations'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('o_order_cost'))
            rec.operation_budget = ope_line
        return rec.operation_budget

    def _compute_material_budget(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.materials'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('m_order_cost'))
            rec.material_budget = ope_line
        return rec.material_budget

    def _compute_expense_budget(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.expenses'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('e_order_cost'))
            rec.expense_budget = ope_line
        return rec.expense_budget

    def _compute_plan_produce_amount(self):
        for rec in self:
            sal_line = sum(
                self.env['farm.produce'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('p_order_cost'))
            rec.plan_produce_amount = sal_line
        return rec.plan_produce_amount

    def _compute_plan_sales_amount(self):
        for rec in self:
            sal_line = sum(
                self.env['farm.sales'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('s_order_cost'))
            rec.plan_sales_amount = sal_line
        return rec.plan_sales_amount

    def _compute_operations_actual(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.operations'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('vendor_bill_total'))
            rec.operations_actual = ope_line
        return rec.operations_actual

    def _compute_materials_actual(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.materials'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('materials_consumption_account_total'))
            rec.materials_actual = ope_line
        return rec.materials_actual

    def _compute_expenses_actual(self):
        for rec in self:
            expenses_actual = sum(
                self.env['farm.expenses'].search([
                    ('projects_id', '=', rec.id)
                ]).mapped('expenses_consumption_account_total')
            )
            rec.expenses_actual = expenses_actual
        return rec.expenses_actual

    def _compute_sum_produce_qty(self):
        for rec in self:
            sum_produce_qty = sum(
                self.env['stock.move.line'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('analytic_account_id', '=', rec.analytic_account_id.id),
                    # ('location_id', '=', self.env.ref('ms_farm.farm_location_produce').id),
                    ('produce_id', '!=', False),
                ]).mapped('qty_done')
            )
            rec.actual_produce_qty = sum_produce_qty
        return rec.actual_produce_qty

    def _compute_actual_produce_amount(self):
        for rec in self:
            produce_debit = sum(
                self.env['account.move.line'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('analytic_account_id', '=', rec.analytic_account_id.id),
                    ('produce_id', '!=', False),
                ]).mapped('debit')
            )
            produce_credit = sum(
                self.env['account.move.line'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('analytic_account_id', '=', rec.analytic_account_id.id),
                    ('produce_id', '!=', False),
                ]).mapped('credit')
            )
            rec.actual_produce_amount = produce_debit + produce_credit
        return rec.actual_produce_amount

    def _compute_average_produce_price(self):
        for rec in self:
            if not rec.actual_produce_qty:
                rec.average_produce_price = 0
                continue
            rec.average_produce_price = rec.actual_produce_amount / rec.actual_produce_qty
        return rec.average_produce_price

    def _compute_cog_produce_price(self):
        for rec in self:
            if not rec.cog_produce_price:
                rec.cog_produce_price = 0
                continue
            rec.cog_produce_price = rec.total_actual / rec.actual_produce_qty
        return rec.cog_produce_price

    def _compute_sum_sales_qty(self):
        for rec in self:
            sum_sales_qty = sum(
                self.env['account.move.line'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('analytic_account_id', '=', rec.analytic_account_id.id),
                    # ('move_type', '=', 'out_invoice'),
                    ('sales_id', '!=', False),
                ]).mapped('quantity')
            )
            rec.actual_sales_qty = sum_sales_qty
        return rec.actual_sales_qty

    def _compute_actual_sales_amount(self):
        for rec in self:
            sales_debit = sum(
                self.env['account.move.line'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('analytic_account_id', '=', rec.analytic_account_id.id),
                    ('sales_id', '!=', False),
                ]).mapped('debit')
            )
            sales_credit = sum(
                self.env['account.move.line'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('analytic_account_id', '=', rec.analytic_account_id.id),
                    ('sales_id', '!=', False),
                ]).mapped('credit')
            )
            rec.actual_sales_amount = sales_debit + sales_credit
        return rec.actual_sales_amount

    def _compute_average_sales_price(self):
        for rec in self:
            if not rec.actual_sales_qty:
                rec.average_sales_price = 0
                continue
            rec.average_sales_price = rec.actual_sales_amount / rec.actual_sales_qty
        return rec.average_sales_price

    def _compute_cog_sales_price(self):
        for rec in self:
            if not rec.cog_sales_price:
                rec.cog_sales_price = 0
                continue
            rec.cog_sales_price = rec.total_actual / rec.actual_sales_qty
        return rec.cog_sales_price

    # -------------------------------------------------------------------------
    # CREATE METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.projects') or _('New')
        return super(farm_projects, self).create(vals)

    def create_project_product(self):
        # if it is existed and send error message
        new_name = self.project_group_id.name + " " + self.short_name
        search_name = self.env['product.template'].search([
            ('name', '=', new_name)
        ])
        if search_name:
            raise UserError(_('Product already exist in the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        # elif create
        product_vals = dict(
            categ_id = self.category_id.id,
            detailed_type = 'product',
            name = new_name,
            projects_id = self.id,
            default_code = self.name + " " + self.short_name,
            standard_price = self.buy_sell_price,
            list_price = self.buy_sell_price,
        )
        new_product = self.env['product.template'].create(product_vals)
        self.create_lock = True
        self.product_id = new_product.id
        return new_product

    def create_project_analytic_account(self):
        # if it is existed and send error message
        new_name = self.project_group_id.name + " " + self.short_name
        search_name = self.env['account.analytic.account'].search([
            ('name', '=', new_name)
        ])
        if search_name:
            raise UserError(_('Product already exist in the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        # elif create
        analytic_account_vals = dict(
            name = new_name,
            project_reference = '% s,% s' % ('farm.projects', self.id),
        )
        new_analytic_account = self.env['account.analytic.account'].create(analytic_account_vals)
        self.analytic_account_id = '% s,% s' % ('account.analytic.account', new_analytic_account.id)
        return

    # -------------------------------------------------------------------------
    # Call Views METHODS
    # -------------------------------------------------------------------------

    def action_open_operation_orders_timeframe(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orders',
            'res_model': 'farm.operations',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'calendar,graph,tree,form',
            'target': 'new'
        }

    def action_open_material_orders_timeframe(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orders',
            'res_model': 'farm.materials',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'calendar,graph,tree,form',
            'target': 'new'
        }

    def action_open_expense_orders_timeframe(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orders',
            'res_model': 'farm.expenses',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'calendar,graph,tree,form',
            'target': 'new'
        }

    def action_open_produce_orders_timeframe(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orders',
            'res_model': 'farm.produce',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'calendar,graph,tree,form',
            'target': 'new'
        }

    def action_open_sales_orders_timeframe(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orders',
            'res_model': 'farm.sales',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'calendar,graph,tree,form',
            'target': 'new'
        }

    def action_open_operation_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Operation Orders',
            'res_model': 'farm.operations',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_projects_id': self.id,
                        'default_user_id': self.user_id.id},
            'target': 'new'
        }

    def action_open_material_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Orders',
            'res_model': 'farm.materials',
            'domain': [('materials_id', '=', self.id)],
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_projects_id': self.id,
                        'default_user_id': self.user_id.id},
            'target': 'new'
        }

    def action_open_sales_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Orders',
            'res_model': 'farm.sales',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_projects_id': self.id,
                        'default_user_id': self.user_id.id},
            'target': 'new'
        }

    def action_open_produce_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Produce Orders',
            'res_model': 'farm.produce',
            'domain': [('projects_id', '=', self.id)],
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_projects_id': self.id,
                        'default_user_id': self.user_id.id},
            'target': 'new'
        }


class farm_project_group(models.Model):
    _name = 'farm.project.group'
    _description = 'Create a Group of project like Calf, Poultry , Grape , fruit ,etc.'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string = 'Group Name',
        required = True,
        help = "Enter the name",
        translate = True,
        tracking = True)
    description = fields.Text(
        string = 'Description',
        required = False,
        help = "Enter the description",
        translate = True,
        tracking = True)


class stockPicking(models.Model):
    _inherit = 'stock.move'

    reference_record = fields.Reference(
        selection = [('farm.operations', 'Operation Order'),
                     ('farm.produce', 'Produce Order')],
        string = 'Order Reference')


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    project_reference = fields.Reference(
        selection = [
            ('farm.projects', 'Project')
        ],
        string = 'Project')
