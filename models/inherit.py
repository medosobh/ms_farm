from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    location_id = fields.Many2one(
        comodel_name = 'stock.location',
        string = "Stock Consume Location",
        check_company = True,
        required = False)
    company_id = fields.Many2one(
        comodel_name = 'res.company',
        string = 'Company',
        change_default = True,
        default = lambda self: self.env.company,
        required = False,
        readonly = True)
    type = fields.Selection([
        ('product', 'Storable Product'),
        ('service', 'Service'),
        ('consu', 'Consumable')],
        string = 'Product Type',
        readonly = False,
        copy = False,
        default = 'product')
    order_type = fields.Selection([
        ('service', 'Service'),
        ('material', 'Material'),
        ('expense', 'Expense'),
        ('produce', 'Produce'),
        ('sales', 'Sales')],
        string = 'Order Type',
        readonly = False,
        copy = False)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    projects_id = fields.Many2one(
        comodel_name = 'farm.projects',
        string = 'Project'
    )
    equipments_id = fields.Many2one(
        comodel_name = 'farm.equipments',
        string = 'Equipment'
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _anglo_saxon_sale_move_lines(
            self,
            name,
            product,
            uom,
            qty,
            price_unit,
            currency=False,
            amount_currency=False,
            fiscal_position=False,
            account_analytic=False,
            analytic_tags=False,
    ):
        res = super()._anglo_saxon_sale_move_lines(
            name,
            product,
            uom,
            qty,
            price_unit,
            currency = currency,
            amount_currency = amount_currency,
            fiscal_position = fiscal_position,
            account_analytic = account_analytic,
            analytic_tags = analytic_tags,
        )
        if res:
            res[0]["account_analytic_id"] = account_analytic and account_analytic.id
            res[0]["analytic_tag_ids"] = (
                    analytic_tags
                    and analytic_tags.ids
                    and [(6, 0, analytic_tags.ids)]
                    or False
            )
        return res


class StockPicking(models.Model):
    _inherit = "stock.picking"

    analytic_account_id = fields.Many2one(
        comodel_name = "account.analytic.account",
        string = "Analytic Account")
    materials_id = fields.Many2one(
        comodel_name = "farm.materials",
        string = "Material Order")
    produce_id = fields.Many2one(
        comodel_name = "farm.produce",
        string = "Produce Order")
    reference_record = fields.Reference(
        selection = [('farm.operations', 'Operation Order'),
                     ('farm.produce', 'Produce Order')],
        string = 'Order Reference')


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one(
        comodel_name = "account.analytic.account",
        string = "Analytic Account")
    materials_id = fields.Many2one(
        comodel_name = "farm.materials",
        string = "Material Order")
    produce_id = fields.Many2one(
        comodel_name = "farm.produce",
        string = "Produce Order")

    def _prepare_account_move_vals(
            self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost
    ):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_vals(
            credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost
        )
        res.update({
            "materials_id": self.materials_id.id,
            "produce_id": self.produce_id.id,
        })
        # fields.append("materials_id")
        # fields.append("produce_id")
        return res

    def _prepare_account_move_line(
            self, qty, cost, credit_account_id, debit_account_id, description
    ):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, description
        )

        for line in res:
            if (
                    line[2]["account_id"]
                    != self.product_id.categ_id.property_stock_valuation_account_id.id
            ):
                # Add analytic account in debit line
                if self.analytic_account_id:
                    line[2].update({
                        "analytic_account_id": self.analytic_account_id.id,
                        "materials_id": self.materials_id.id,
                        "produce_id": self.produce_id.id,
                    })
        return res

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        fields = super()._prepare_merge_moves_distinct_fields()
        fields.append("analytic_account_id")
        fields.append("materials_id")
        fields.append("produce_id")
        return fields


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_account_id = fields.Many2one(
        related = "move_id.analytic_account_id")
    materials_id = fields.Many2one(
        related = "move_id.materials_id")
    produce_id = fields.Many2one(
        related = "move_id.produce_id")


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    analytic_account_id = fields.Many2one(
        comodel_name = "account.analytic.account",
        string = "Analytic Account")
    materials_id = fields.Many2one(
        comodel_name = "farm.materials",
        string = "Material Order")
    produce_id = fields.Many2one(
        comodel_name = "farm.produce",
        string = "Produce Order")

    def _prepare_move_values(self):
        res = super()._prepare_move_values()
        res.update(
            {
                "analytic_account_id": self.analytic_account_id.id,
                "materials_id": self.materials_id.id,
                "produce_id": self.produce_id.id,
            }
        )
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    materials_id = fields.Many2one(
        comodel_name = 'farm.materials',
        string = "Farm Material")
    produce_id = fields.Many2one(
        comodel_name = 'farm.produce',
        string = "Farm Produce")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # expense already maintained in he.expense model
    equipments_id = fields.Many2one(
        comodel_name = 'farm.equipments',
        string = "Farm Equipment")
    operations_id = fields.Many2one(
        comodel_name = 'farm.operations',
        string = "Farm Operation")
    materials_id = fields.Many2one(
        comodel_name = 'farm.materials',
        string = "Farm Material")
    produce_id = fields.Many2one(
        comodel_name = 'farm.produce',
        string = "Farm Produce")
    sales_id = fields.Many2one(
        comodel_name = 'farm.sales',
        string = "Farm Sales")
    move_type = fields.Selection(
        related = "move_id.move_type")


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    project_reference = fields.Reference(
        selection = [
            ('farm.projects', 'Project')
        ],
        string = 'Project')
