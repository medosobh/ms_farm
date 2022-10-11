from datetime import date, datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class farm_projects(models.Model):
    _name = 'farm.projects'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Create a project to followup all operations'
    _sql_constraints = [
        ('short_name_uniq', 'unique(short_name)', "A short name can only be assigned to one equipments !"),
    ]

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

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('start_date', 'p_days', 'close_date')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.p_days):
                r.end_date = r.start_date
                continue
            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            p_days = timedelta(days = r.p_days, seconds = 0)
            r.end_date = r.start_date + p_days

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.p_days = (r.end_date - r.start_date).days + 1

    def _get_time_gone(self):
        for r in self:
            if not r.start_date:
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.g_days = (date.today() - r.start_date).days + 1

    def _get_actual_gone(self):
        for r in self:
            if not (r.start_date and r.close_date):
                r.close_date = r.end_date
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.a_days = (r.close_date - r.start_date).days + 1

    def _compute_operations_count(self):
        for rec in self:
            operations_count = self.env['farm.operations'].search_count([('projects_id', '=', rec.id)])
            rec.operations_count = operations_count

    def _compute_materials_count(self):
        for rec in self:
            materials_count = self.env['farm.materials'].search_count([('projects_id', '=', rec.id)])
            rec.materials_count = materials_count

    def _compute_produce_count(self):
        for rec in self:
            produce_count = self.env['farm.produce'].search_count([('projects_id', '=', rec.id)])
            rec.produce_count = produce_count

    def _compute_sales_count(self):
        for rec in self:
            sales_count = self.env['farm.sales'].search_count([('projects_id', '=', rec.id)])
            rec.sales_count = sales_count

    def _compute_operation_budget(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.operations'].search([('projects_id', '=', rec.id)]).mapped('o_order_cost'))
            rec.operation_budget = ope_line
        return rec.operation_budget

    def _compute_material_budget(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.materials'].search([('projects_id', '=', rec.id)]).mapped('m_order_cost'))
            rec.material_budget = ope_line
        return rec.material_budget

    def _compute_plan_produce_amount(self):
        for rec in self:
            sal_line = sum(
                self.env['farm.produce'].search([('projects_id', '=', rec.id)]).mapped('p_order_cost'))
            rec.plan_produce_amount = sal_line
        return rec.plan_produce_amount

    def _compute_plan_sales_amount(self):
        for rec in self:
            sal_line = sum(
                self.env['farm.sales'].search([('projects_id', '=', rec.id)]).mapped('s_order_cost'))
            rec.plan_sales_amount = sal_line
        return rec.plan_sales_amount

    def _compute_operations_actual(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.operations'].search([('projects_id', '=', rec.id)]).mapped('vendor_bill_total'))
            rec.operations_actual = ope_line
        return rec.operations_actual

    def _compute_materials_actual(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.materials'].search([
                    ('projects_id', '=', rec.id)]).mapped('materials_consumption_account_total'))
            rec.materials_actual = ope_line
        return rec.materials_actual

    def _compute_actual_produce_amount(self):
        for rec in self:
            ope_line = sum(
                self.env['farm.produce'].search([
                    ('projects_id', '=', rec.id)]).mapped('produce_consumption_account_total'))
            rec.actual_produce_amount = ope_line
        return rec.actual_produce_amount

    def _compute_actual_sales_amount(self):
        for rec in self:
            sal_line = sum(
                self.env['farm.sales'].search([('projects_id', '=', rec.id)]).mapped('customer_invoice_total'))
            rec.actual_sales_amount = sal_line
        return rec.actual_sales_amount

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

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.projects') or _('New')
        return super(farm_projects, self).create(vals)

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
    project_type = fields.Selection(
        [('create', 'Create an Pio/Asset'), ('operate', 'Operate an Pio/Asset')],
        required = True,
        string = 'Type',
        default = 'operate',
        tracking = True)
    project_group_id = fields.Many2one(
        comodel_name = 'farm.project.group',
        string = 'Project Group')
    user_id = fields.Many2one(
        'res.users', string = "Project Man",
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
        default = datetime.today(),
        inverse = '_get_time_gone')
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
    actual_produce_qty = fields.Float(
        string = 'Produce Act. Qty',
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
        'farm.operations',
        string = "Project Operations")
    operations_ids = fields.One2many(
        'farm.operations',
        'projects_id',
        string = "Operation Orders")
    operations_count = fields.Integer(
        string = "Operation Count",
        compute = '_compute_operations_count')
    materials_id = fields.Many2one(
        'farm.materials',
        string = "Project Materials")
    materials_ids = fields.One2many(
        'farm.materials',
        'projects_id',
        string = "Material Orders")
    materials_count = fields.Integer(
        string = "Material Count",
        compute = '_compute_materials_count')
    produce_id = fields.Many2one(
        'farm.produce',
        string = "Produce Orders")
    produce_ids = fields.One2many(
        'farm.produce',
        'projects_id',
        string = "Produce Orders")
    produce_count = fields.Integer(
        string = "Produce Count",
        compute = '_compute_produce_count')
    sales_id = fields.Many2one(
        'farm.sales',
        string = "Sales Orders")
    sales_ids = fields.One2many(
        'farm.sales',
        'projects_id',
        string = "Sales Orders")
    sales_count = fields.Integer(
        string = "Sales Count",
        compute = '_compute_sales_count')
    company_id = fields.Many2one(
        'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        related = 'company_id.currency_id',
        readonly = True,
        ondelete = 'set null',
        help = "Used to display the currency when tracking monetary values")
    locations_ids = fields.Many2many(
        'farm.locations',
        'projects_id',
        string = "Produce Orders")


class farm_project_group(models.Model):
    _name = 'farm.project.group'
    _description = 'Create a Group of project like Calf, Poultry , Grape , fruit ,etc.'

    name = fields.Char(string = 'Group Name',
                       required = True,
                       help = "Enter the name",
                       translate = True,
                       tracking = True)
    description = fields.Text(string = 'Description',
                              required = False,
                              help = "Enter the description",
                              translate = True,
                              tracking = True)


class farm_locations(models.Model):
    _name = 'farm.locations'
    _description = 'Manage project location'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string = 'Location',
                       required = True)
    complete_name = fields.Char(
        'Complete Name',
        compute = '_compute_complete_name',
        recursive = True,
        store = True)
    space = fields.Float(string = 'Space in acre')
    parent_id = fields.Many2one('farm.locations',
                                'Parent Location',
                                index = True,
                                ondelete = 'cascade')
    parent_path = fields.Char(index = True)
    child_id = fields.One2many('farm.locations', 'parent_id', 'Child location')
    space_sum = fields.Float(
        '# Acre',
        compute = '_compute_space_sum',
        help = "The Acre space under this location (Does not consider the children location)")

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    def _space_sum(self):
        self.space_sum = 1
        # read_group_res = self.env['farm.locations'].read_group([('locat_id', 'child_of', self.ids)], ['locat_id'], ['locat_id'])
        # group_data = dict((data['locat_id'][0], data['locat_id_sum']) for data in read_group_res)
        # for locat in self:
        #     space_sum = 0
        #     for sub_locat_id in locat.search([('id', 'child_of', locat.ids)]).ids:
        #         space_sum += group_data.get(sub_locate_id, 0)
        #     categ.space_sum = space_sum

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    def name_get(self):
        if not self.env.context.get('hierarchical_naming', True):
            return [(record.id, record.name) for record in self]
        return super().name_get()


class stockPicking(models.Model):
    _inherit = 'stock.move'

    reference_record = fields.Reference(selection = [('farm.operations', 'Operation Order'),
                                                     ('farm.produce', 'Produce Order')],
                                        string = 'Order Reference')


