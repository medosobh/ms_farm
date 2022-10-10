from odoo import fields, models, api, _
from odoo.exceptions import UserError


class farm_produce(models.Model):
    _name = 'farm.produce'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Handel all produce order'
    _order = 'issue_date'

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('produce_order_line_ids')
    def _compute_produce_order_cost(self):
        self.p_order_cost = 0
        for rec in self:
            pline = sum(self.env['farm.produce.oline'].search([('produce_id', '=', rec.id)]).mapped('price_subtotal'))
            rec.p_order_cost = pline
        return rec.p_order_cost

    def _compute_stock_move_count(self):
        for rec in self:
            count = self.env['stock.picking'].search_count([('origin', '=', rec.name)])
            rec.produce_consumption_count = count
        return rec.produce_consumption_count

    def _compute_account_move_count(self):
        am_count = 0
        fam_count = 0
        for mo_rec in self:
            sp_count = self.env['stock.picking'].search([('origin', '=', mo_rec.name)])

        for sm_rec in sp_count:
            sm_count = self.env['stock.move'].search([('picking_id', '=', sm_rec.id)])
            am_count = self.env['account.move'].search_count([('stock_move_id', '=', sm_count.id)])
            fam_count = fam_count + am_count

        mo_rec.produce_consumption_account_count = fam_count
        return mo_rec.produce_consumption_account_count

    def _compute_account_move_total(self):
        am_total = 0
        fam_total = 0
        for mo_rec in self:
            sp_count = self.env['stock.picking'].search([('origin', '=', mo_rec.name)])

        for sm_rec in sp_count:
            sm_count = self.env['stock.move'].search([('picking_id', '=', sm_rec.id)])
            am_total = sum(
                self.env['account.move'].search([('stock_move_id', '=', sm_count.id)]).mapped('amount_total_signed'))
            fam_total = fam_total + am_total

        mo_rec.produce_consumption_account_total = fam_total
        return mo_rec.produce_consumption_account_total

    # -------------------------------------------------------------------------
    # Create METHODS
    # -------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.produce') or _('New')
        return super(farm_produce, self).create(vals)

    def button_farm_stock_in(self):
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'direct')
        warehouse = self.stock_warehouse

        if not warehouse:
            raise UserError(_('Please define a warehouse for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        picking_vals = {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
            'location_id': self.location_id.id,
            'move_type': move_type,
            'note': self.notes,
            'scheduled_date': self.issue_date,
            'date_deadline': self.issue_date,
            'user_id': self.user_id.id,
            'state': 'draft',
            'move_ids_without_package': [(0, 0, {
                'name': self.produce_order_line_ids.name or '',
                'product_id': self.produce_order_line_ids.product_id.id,
                'product_uom_qty': self.produce_order_line_ids.qty,
                'product_uom': self.produce_order_line_ids.product_uom.id,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                # 'picking_id': picking.id,
                'state': 'draft',
                'company_id': self.company_id.id,
                'picking_type_id': self.picking_type_id.id,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': self.picking_type_id.warehouse_id.id,
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

    name = fields.Char(
        string = 'Produce Ref',
        index = True,
        readonly = True,
        tracking = True,
        default = lambda x: _('New'))
    state = fields.Selection([
        ('order', 'Invoicing'),
        ('lock', 'Locked')],
        string = 'State', readonly = False, copy = False,
        tracking = True, default = 'order')
    category_id = fields.Many2one(
        'product.category',
        required = True,
        string = 'Product Category')
    projects_id = fields.Many2one(
        'farm.projects',
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
        'res.partner',
        string = 'Partner')
    stock_warehouse = fields.Many2one(
        'stock.warehouse',
        required = True,
        string = 'Warehouse')
    location_id = fields.Many2one(
        'stock.location',
        "Destination Location",
        default = lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        domain = [('usage', '=', 'internal')],
        check_company = True,
        required = True)
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        "Stock Picking Type",
        default = lambda self: self.env.ref('ms_farm.farm_stock_produce').id,
        required = True)
    p_order_cost = fields.Float(
        string = 'Order Cost',
        compute = '_compute_produce_order_cost',
        store = True)
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)
    user_id = fields.Many2one(
        'res.users',
        string = "Operation Man",
        required = True)
    notes = fields.Html(
        'Terms and Conditions')
    produce_order_line_ids = fields.One2many(
        'farm.produce.oline',
        'produce_id',
        string = "produce order lines")
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        related = 'company_id.currency_id',
        readonly = True,
        ondelete = 'set null',
        help = "Used to display the currency when tracking monetary values")
    produce_consumption_count = fields.Integer(
        string = "Material Moves Count",
        compute = '_compute_stock_move_count')
    produce_consumption_account_count = fields.Integer(
        string = "Material Moves Count",
        compute = '_compute_account_move_count')
    produce_consumption_account_total = fields.Integer(
        string = "Material Moves Total",
        compute = '_compute_account_move_total')


class farm_produce_oline(models.Model):
    _name = 'farm.produce.oline'
    _description = 'handel all produce order line'

    @api.depends('price_unit', 'qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty

    name = fields.Text(
        string = 'Description',
        required = True)
    sequence = fields.Integer(
        string = 'Sequence',
        default = 10)
    product_id = fields.Many2one(
        'product.product',
        required = True,
        domain = "[('categ_id', '=', categ_id)]")
    categ_id = fields.Many2one(
        related = 'produce_id.category_id',
        string = 'Category')
    price_unit = fields.Float(
        related = 'product_id.standard_price',
        string = 'Price')
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related = 'product_id.uom_id',
        domain = "[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float(
        'Quantity')
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        related = 'produce_id.company_id',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    currency_id = fields.Many2one(
        'res.currency',
        string = 'Currency',
        related = 'produce_id.currency_id',
        readonly = True,
        help = "Used to display the currency when tracking monetary values")
    note = fields.Char(
        'Short Note')
    price_subtotal = fields.Monetary(
        string = 'Subtotal',
        compute = '_compute_subtotal',
        currency_field = 'currency_id',
        store = True)
    produce_id = fields.Many2one(
        'farm.produce', string = 'Produce Order')
    equipments_id = fields.Many2one(
        'farm.equipments',
        string = 'Equipments',
        related = 'product_id.equipments_id')
