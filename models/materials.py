from odoo import fields, models, api, _
from odoo.exceptions import UserError


class FarmMaterials(models.Model):
    _name = 'farm.materials'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Material Orders'
    _check_company_auto = True
    _order = 'issue_date'

    name = fields.Char(
        string='Material Ref',
        index=True,
        readonly=True,
        tracking=True,
        default=lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Order'),
        ('lock', 'Locked')],
        string='State', readonly=False, copy=False,
        tracking=True, default='order')
    category_id = fields.Many2one(
        comodel_name='product.category',
        required=True,
        domain=[('order_type', '=', 'material')],
        string='Product Category')
    projects_id = fields.Many2one(
        comodel_name='farm.projects',
        required=True,
        tracking=True)
    short_name = fields.Char(
        related='projects_id.short_name',
        store=True)
    issue_date = fields.Date(
        string='Date',
        default=fields.Datetime.today,
        tracking=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')
    stock_warehouse = fields.Many2one(
        comodel_name='stock.warehouse',
        required=True,
        string='Warehouse')
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Source Location',
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        domain=[('usage', '=', 'internal')],
        check_company=True,
        required=True)
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Stock Picking Type',
        default=lambda self: self.env.ref(
            'ms_farm.farm_location_fertilize').id,
        required=True)
    m_order_cost = fields.Monetary(
        string='Order Cost',
        compute='_compute_material_order_cost',
        currency_field='currency_id',
        store=True)
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Order Man",
        required=True)
    notes = fields.Html(
        string='Terms and Conditions')
    materials_order_line_ids = fields.One2many(
        comodel_name='farm.materials.oline',
        inverse_name='materials_id',
        string="order lines")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        change_default=True,
        default=lambda self: self.env.company,
        required=False,
        readonly=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        ondelete='set null',
        help="Used to display the currency when tracking monetary values")
    materials_consumption_count = fields.Integer(
        string="Material Moves Count",
        compute='_compute_stock_move_count')
    materials_consumption_account_count = fields.Integer(
        string="Material Moves Count",
        compute='_compute_account_move_count')
    materials_consumption_account_total = fields.Integer(
        string="Material Moves Total",
        compute='_compute_account_move_total')
    analytic_account_id = fields.Reference(
        related='projects_id.analytic_account_id')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('materials_order_line_ids')
    def _compute_material_order_cost(self):
        for rec in self:
            oline = sum(
                self.env['farm.materials.oline'].search([
                    ('materials_id', '=', rec.id)
                ]).mapped('price_subtotal'))
            rec.m_order_cost = oline

    def _compute_stock_move_count(self):
        for rec in self:
            count = self.env['stock.move'].search_count([
                ('materials_id', '=', rec.id)
            ])
            rec.materials_consumption_count = count

    def _compute_account_move_count(self):
        fam_count = 0
        for mo_rec in self:
            fam_count = self.env['account.move'].search_count([
                ('materials_id', '=', mo_rec.id)
            ])

        mo_rec.materials_consumption_account_count = fam_count

    def _compute_account_move_total(self):
        for rec in self:
            total_debit = sum(
                self.env['account.move.line'].search([
                    ('materials_id', '=', rec.id)
                ]).mapped('debit')
            )
            total_credit = sum(
                self.env['account.move.line'].search([
                    ('materials_id', '=', rec.id)
                ]).mapped('credit')
            )
        rec.materials_consumption_account_total = total_debit + total_credit

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'farm.materials') or _('New')
        return super(FarmMaterials, self).create(vals)

    def button_farm_stock_out(self):
        self.ensure_one()

        # check analytic_account_id created
        analytic = self.analytic_account_id
        if not analytic:
            raise UserError(_('Please define an analytic account for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        move_type = self._context.get('default_move_type', 'direct')
        warehouse = self.stock_warehouse

        if not warehouse:
            raise UserError(_('Please define a warehouse for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        picking_vals = {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'location_dest_id': self.category_id.location_id.id,
            'location_id': self.location_id.id,
            'move_type': move_type,
            'note': self.notes,
            'scheduled_date': self.issue_date,
            'date_deadline': self.issue_date,
            'user_id': self.user_id.id,
            'state': 'draft',
            'materials_id': self.id,
            'move_ids_without_package': [(0, 0, {
                'name': self.materials_order_line_ids.name or '',
                'product_id': self.materials_order_line_ids.product_id.id,
                'product_uom_qty': self.materials_order_line_ids.qty,
                'product_uom': self.materials_order_line_ids.product_uom.id,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.category_id.location_id.id,
                # 'picking_id': self.picking.id,
                'state': 'draft',
                'company_id': self.company_id.id,
                'picking_type_id': self.picking_type_id.id,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': self.picking_type_id.warehouse_id.id,
                'analytic_account_id': self.analytic_account_id.id,
                'materials_id': self.id,
            })]
        }
        create_picking = self.env['stock.picking'].create(picking_vals)
        action = {
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('stock.view_picking_form').id,
            'res_model': 'stock.picking',
            'res_id': create_picking.id,
            'domain': [('origin', '=', self.name)],
            'view_mode': 'form',
            'context': {},
            'target': 'current'
        }
        return action

    def action_stock_picking_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Moves',
            'res_model': 'stock.picking',
            'domain': [('origin', '=', self.name)],
            'view_mode': 'tree,form',
            'context': {},
            'target': 'current'
        }


class FarmMaterialsOline(models.Model):
    _name = 'farm.materials.oline'
    _description = 'Material Order Line'

    sequence = fields.Integer(
        string='Sequence',
        default=10)
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
        domain="[('categ_id', '=', categ_id)]")
    name = fields.Text(
        string='Description',
        required=False)
    categ_id = fields.Many2one(
        related='materials_id.category_id',
        string='Category')
    price_unit = fields.Float(
        string='Price')
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        domain="[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float(
        'Quantity')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='materials_id.company_id',
        change_default=True,
        default=lambda self: self.env.company,
        required=False,
        readonly=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='materials_id.currency_id',
        readonly=True,
        help="Used to display the currency when tracking monetary values")
    note = fields.Char(
        string='Short Note')
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        currency_field='currency_id',
        store=True)
    materials_id = fields.Many2one(
        comodel_name='farm.materials',
        string='Materials')

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
