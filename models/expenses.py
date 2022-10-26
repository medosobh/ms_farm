from odoo import fields, models, api, _


class farm_expenses(models.Model):
    _name = 'farm.expenses'
    _description = 'Budget General Expenses'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date'

    name = fields.Char(
        string = 'expense Ref',
        index = True,
        readonly = True,
        tracking = True,
        default = lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Order'),
        ('lock', 'Locked')],
        string = 'State',
        readonly = False,
        copy = False,
        tracking = True,
        default = 'order')
    category_id = fields.Many2one(
        comodel_name = 'product.category',
        required = True,
        domain = [('order_type', '=', 'expense')],
        string = 'Product Category')
    projects_id = fields.Many2one(
        comodel_name = 'farm.projects',
        required = True,
        tracking = True)
    short_name = fields.Char(
        related = 'projects_id.short_name',
        store = True)
    issue_date = fields.Date(
        string = 'Date',
        default = fields.Datetime.today,
        tracking = True)
    partner_id = fields.Many2one(
        comodel_name = 'res.partner',
        string = 'Partner')
    stock_warehouse = fields.Many2one(
        comodel_name = 'stock.warehouse',
        required = False,
        string = 'Warehouse')
    location_id = fields.Many2one(
        comodel_name = 'stock.location',
        string = 'Source Location',
        default = lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        domain = [('usage', '=', 'internal')],
        check_company = True,
        required = False)
    picking_type_id = fields.Many2one(
        comodel_name = 'stock.picking.type',
        string = 'Stock Picking Type',
        default = lambda self: self.env.ref('ms_farm.farm_location_fertilize').id,
        required = False)
    e_order_cost = fields.Monetary(
        string = 'Budget Cost',
        compute = '_compute_expense_order_cost',
        currency_field = 'currency_id',
        store = True)
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)
    user_id = fields.Many2one(
        comodel_name = 'res.users',
        string = "Order Man",
        required = True)
    notes = fields.Html(
        string = 'Terms and Conditions')
    expenses_order_line_ids = fields.One2many(
        comodel_name = 'farm.expenses.oline',
        inverse_name = 'expenses_id',
        string = "order lines")
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        comodel_name = 'res.currency',
        string = 'Currency',
        related = 'company_id.currency_id',
        readonly = True,
        ondelete = 'set null',
        help = "Used to display the currency when tracking monetary values")
    expenses_consumption_count = fields.Integer(
        string = "expense Moves Count",
        compute = '_compute_expense_ticket_count')
    expenses_consumption_account_count = fields.Integer(
        string = "expense Moves Count",
        compute = '_compute_account_move_count')
    expenses_consumption_account_total = fields.Integer(
        string = "expense Moves Total",
        compute = '_compute_account_move_total')
    analytic_account_id = fields.Reference(
        related = 'projects_id.analytic_account_id')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('expenses_order_line_ids')
    def _compute_expense_order_cost(self):
        for rec in self:
            oline = sum(
                self.env['farm.expenses.oline'].search([('expenses_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.e_order_cost = oline
        return rec.e_order_cost

    def _compute_expense_ticket_count(self):
        for rec in self:
            count = self.env['hr.expense'].search_count([('analytic_account_id', '=', rec.analytic_account_id.id)])
            rec.expenses_consumption_count = count
        return rec.expenses_consumption_count

    def _compute_account_move_count(self):
        for mo_rec in self:
            sp_count = self.env['account.move.line'].search_count([
                ('expense_id', '!=', False),
                ('analytic_account_id', '=', mo_rec.analytic_account_id.id)
            ])

        mo_rec.expenses_consumption_account_count = sp_count
        return mo_rec.expenses_consumption_account_count

    def _compute_account_move_total(self):
        for mo_rec in self:
            debit_total = sum(
                self.env['account.move.line'].search([
                    ('expense_id', '!=', False),
                    ('analytic_account_id', '=', mo_rec.analytic_account_id.id)
                ]).mapped('debit'))
            credit_total = sum(
                self.env['account.move.line'].search([
                    ('expense_id', '!=', False),
                    ('analytic_account_id', '=', mo_rec.analytic_account_id.id)
                ]).mapped('credit'))
            fam_total = debit_total - credit_total
        self.expenses_consumption_account_total = fam_total
        return self.expenses_consumption_account_total

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.expenses') or _('New')
        return super(farm_expenses, self).create(vals)

    def button_farm_expense_issue(self):
        self.ensure_one()
        print('expense ticket')
        return

    def action_expense_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expenses to Report',
            'res_model': 'hr.expense',
            'domain': [('analytic_account_id', '=', self.analytic_account_id.id)],
            'view_mode': 'tree,form',
            'context': {},
            'target': 'current'
        }

    def action_expense_account_line(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expenses to Report',
            'res_model': 'account.move.line',
            'domain': [
                ('expense_id', '!=', False),
                ('analytic_account_id', '=', self.analytic_account_id.id)
            ],
            'view_mode': 'tree,form',
            'context': {},
            'target': 'current'
        }


class farm_expenses_oline(models.Model):
    _name = 'farm.expenses.oline'
    _description = 'expense order line'

    name = fields.Text(
        string = 'Description',
        required = False)
    state = fields.Selection(
        related = 'expenses_id.state', )
    sequence = fields.Integer(
        string = 'Sequence',
        default = 10)
    product_id = fields.Many2one(
        comodel_name = 'product.product',
        required = True,
        domain = "[('categ_id', '=', categ_id)]")
    categ_id = fields.Many2one(
        related = 'expenses_id.category_id',
        string = 'Category')
    price_unit = fields.Float(
        string = 'Price')
    product_uom = fields.Many2one(
        comodel_name = 'uom.uom',
        string = 'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float(
        string = 'Quantity')
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        related = 'expenses_id.company_id',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        comodel_name = 'res.currency',
        string = 'Currency',
        related = 'expenses_id.currency_id',
        readonly = True,
        help = "Used to display the currency when tracking monetary values")
    note = fields.Char(
        string = 'Short Note')
    price_subtotal = fields.Monetary(
        string = 'Subtotal',
        compute = '_compute_subtotal',
        currency_field = 'currency_id',
        store = True)
    expenses_id = fields.Many2one(
        comodel_name = 'farm.expenses',
        string = 'expenses')
    analytic_account_id = fields.Reference(
        related = 'expenses_id.analytic_account_id')
    employee_id = fields.Many2one(
        comodel_name = 'hr.employee',
        string = "Advance to Employee", )
    expense_id = fields.Many2one(
        comodel_name = 'hr.expense',
        string = 'Expense Ref',
        copy = False,
        help = "Expense where the move line come from")

    @api.onchange('product_id')
    def onchange_price_unit(self):
        if not self.product_id:
            self.price_unit = 0
            return
        self.price_unit = self.product_id.standard_price

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty

    def button_farm_expense_issue(self):
        # This will make sure we have on record, not multiple records.
        self.ensure_one()
        if not self.employee_id.id:
            expense_vals = {
                'state': 'draft',
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': self.qty,
                'unit_amount': self.price_unit,
                'payment_mode': 'company_account',
                'analytic_account_id': self.analytic_account_id.id,
            }
        else:
            expense_vals = {
                'state': 'draft',
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': self.qty,
                'unit_amount': self.price_unit,
                'payment_mode': 'own_account',
                'employee_id': self.employee_id.id,
                'analytic_account_id': self.analytic_account_id.id,
            }
        expense = self.env['hr.expense'].create(expense_vals)
        print('expense ticket')
        self.expense_id = expense.id
        return {
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_expense.hr_expense_view_form').id,
            'res_id': expense.id,
        }
