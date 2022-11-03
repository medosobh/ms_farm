from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PioAsset(models.Model):
    _name = 'farm.pioasset'
    _description = 'List of Pio Asset'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'
    _sql_constraints = [
        ('code_uniq', 'unique(code)', "A Code can only be assigned to one Pio-Asset !"),
    ]
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(
        index = True,
        required = True,
    )
    name = fields.Char(
        string = 'Pio Asset Name',
        required = True,
    )
    complete_name = fields.Char(
        string = 'Complete Name',
        compute = '_compute_pioasset_complete_name',
        recursive = True,
        store = True,
    )
    type = fields.Selection(
        string = 'Type',
        selection = [
            ('count', 'Countable'),
            ('uncount', 'Uncountable'),
        ]
    )
    group = fields.Many2one(
        comodel_name = 'farm.project.group',
        string = 'Group',
        index = True,
    )
    parent_id = fields.Many2one(
        comodel_name = 'farm.pioasset',
        string = 'Parent Pio Asset',
        index = True,
        ondelete = 'cascade'
    )
    parent_path = fields.Char(
        index = True
    )
    child_id = fields.One2many(
        comodel_name = 'farm.pioasset',
        inverse_name = 'parent_id',
        string = 'Child PioAsset'
    )
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True
    )
    currency_id = fields.Many2one(
        comodel_name = 'res.currency',
        string = 'Currency',
        related = 'company_id.currency_id',
        readonly = True,
        ondelete = 'set null',
        help = "Used to display the currency when tracking monetary values"
    )
    control_ids = fields.One2many(
        comodel_name = 'farm.control',
        inverse_name = 'pioasset_id',
        string = 'Control Tickets'
    )
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_pioasset_complete_name(self):
        for pioasset in self:
            if pioasset.parent_id:
                pioasset.complete_name = '%s / %s' % (pioasset.parent_id.complete_name, pioasset.name)
            else:
                pioasset.complete_name = pioasset.name

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


class events(models.Model):
    _name = 'farm.event'
    _description = 'Events'

    name = fields.Char(
        string = 'Event'
    )
    description = fields.Text(
        string = 'Description'
    )
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True
    )


class action(models.Model):
    _name = 'farm.action'
    _description = 'Action'

    name = fields.Char(
        string = 'Action'
    )
    description = fields.Text(
        string = 'Description'
    )
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True
    )


class FarmControl(models.Model):
    _name = 'farm.control'
    _description = 'Inspect and cure Pio Asset '
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        string = 'State',
        selection = [
            ('draft', 'Draft'),
            ('progress', 'In-Progress'),
            ('schedule', 'Re-Schedule'),
            ('cancel', 'Cancel'),
            ('done', 'Done'),
        ],
        default = 'draft',
        group_expand = '_group_expand_states',
        required = True,
    )
    pioasset_id = fields.Many2one(
        comodel_name = 'farm.pioasset',
        required = True,
        string = 'Pio Asset'
    )
    priority = fields.Selection(
        selection = [
            ('0', 'Normal'),
            ('1', 'Low'),
            ('2', 'High'),
            ('3', 'Very High')
        ],
        string = "Priority",
        help = 'Set the project priority which view first')
    name = fields.Char(
        string = 'Reference',
        default = lambda x: _('New')
    )
    complete_name = fields.Char(
        string = 'Complete Name',
        compute = '_compute_control_complete_name',
        recursive = True,
        store = True)
    init_date = fields.Date(
        string = 'Init Date',
        default = datetime.today(),
        required = True,
    )
    next_date = fields.Date(
        string = 'Next Date',
        default = datetime.today(),
        required = True,
    )
    lead_time = fields.Integer(
        string = 'Lead Time in Days',
        compute = '_get_lead_time'
    )
    event_id = fields.Many2one(
        comodel_name = 'farm.event',
        required = True,
    )
    event_desc = fields.Text(
        comodel_name = 'farm.event',
        string = 'Description',
        related = 'event_id.description',
    )
    action_id = fields.Many2one(
        comodel_name = 'farm.action',
        required = True,
    )
    action_desc = fields.Text(
        comodel_name = 'farm.action',
        string = 'Description',
        related = 'action_id.description',
    )
    what = fields.Text(
        string = 'What?',
        required = True,
    )
    who = fields.Many2one(
        string = 'Who?',
        comodel_name = 'res.users',
        required = True,
    )
    parent_id = fields.Many2one(
        comodel_name = 'farm.control',
        string = 'Parent Ticket',
        index = True,
        ondelete = 'cascade')
    parent_path = fields.Char(
        index = True)
    child_id = fields.One2many(
        comodel_name = 'farm.control',
        inverse_name = 'parent_id',
        string = 'Child Ticket')
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
    active = fields.Boolean(
        string = "Active",
        default = True,
        tracking = True)

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('farm.control') or _('New')
        return super(FarmControl, self).create(vals)

    @api.depends('init_date', 'next_date')
    def _get_lead_time(self):
        self.ensure_one()
        if not (self.init_date or self.next_date or self.next_date < self.init_date):
            self.lead_time = 0
        else:
            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            self.lead_time = (self.next_date - self.init_date).days + 1
        return self.lead_time

    @api.depends('name', 'parent_id.complete_name')
    def _compute_control_complete_name(self):
        for control in self:
            if control.parent_id:
                control.complete_name = '%s / %s' % (control.parent_id.complete_name, control.name)
            else:
                control.complete_name = control.name
