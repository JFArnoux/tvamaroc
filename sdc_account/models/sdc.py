from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, pycompat

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
    
class ResCompany(models.Model):
    _inherit = 'res.company' 
    
    idf = fields.Char(string='Identifiant Fiscal')
    rc = fields.Char(string='Registre du commerce')
    tc = fields.Char(string='Tribunal de commerce')
    itp = fields.Char(string='Patente')
    ice = fields.Char(string='I.C.E')
    cnss = fields.Char(string='CNSS')  
    idfp = fields.Char(string='Identifiant Taxe Professionnelle')
    drp = fields.Char(string='Direction régionale ou préfectorale')
    subdivision = fields.Char(string='Subdivision')
    code_dr = fields.Char(string='Code DR ou DP')
    
    regim_tva = fields.Selection([('1', 'Déclaration mensuelle'), ('2', 'Déclaration trimestrielle')], string= 'Régime T.V.A')
    fait_tva = fields.Selection([('1', 'Encaissement'), ('2', 'Débit')], string= 'Fait générateur TVA')
    
    recette = fields.Char(string='Recette')
    code_recette = fields.Char(string='Code recette')
    raison_s = fields.Char(string='Raison sociale') 
    fj = fields.Char(string='Forme juridique')
    adresse_siege = fields.Char(string='Adresse du siège')
    city_id = fields.Char(string='Ville du siège')
    
    type_lf = fields.Many2one('type.liasse', string= 'Type de liasse fiscale')
    invoice_description = fields.Char(string='Description factures vente par défaut')

    
class TypLiasee(models.Model):
    _name = 'type.liasse'
    
    name=fields.Char(string='Libellé du modèle')
    identifiant=fields.Char(string='Identifiant du modèle')
    type=fields.Char(string='Type de liasse fiscale')
      
    
class Partner(models.Model):
    _inherit = 'res.partner' 
       
    rc = fields.Char(string='Registre du commerce')
    tc = fields.Char(string='Tribunal de commerce')
    ifs = fields.Char(string='Identifiant Fiscal')
    patente = fields.Char(string='Patente')
    ice = fields.Char(string='I.C.E')
    description_facture = fields.Char(string='Description facture')
    

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    description_facture = fields.Char(string='Description facture', related='company_id.invoice_description', readonly=True)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    description_facture = fields.Char(string='Description facture', related='company_id.invoice_description', readonly=True)
        
class PaymentMode(models.Model):
    _name = 'payment.mode'
     
    name=fields.Char(string='Mode de paiement', required=True)
    supplier_def=fields.Boolean(string='Par défaut règlements fournisseurs')
    prohibit=fields.Boolean(string='Interdire')
 
class AccountPayment(models.Model):
    _inherit = "account.payment"
    payment_mode = fields.Many2one('payment.mode',string='Mode de paiement', required=True)
    deadline = fields.Date(string='Échéance')
    number = fields.Char(string='Pièce N°')
    
class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.sheet.register.payment.wizard"
    payment_mode = fields.Many2one('payment.mode',string='Mode de paiement', required=True)
    number = fields.Char(string='Pièce N°')
       
    def _get_payment_vals(self):
        """ Hook for extension """
        return {
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'payment_mode': self.payment_mode.id,
            'number': self.number
        }       
        
        
class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"
    
    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        amount = self._compute_payment_amount(invoices) if self.multi else self.amount
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'payment_mode': self.payment_mode.id,
            'deadline': self.deadline,
            'number': self.number
        }
        

class AccountTax(models.Model):
    _inherit = 'account.tax'   
    code_dgi=fields.Char(string='Code DGI', required=True)
    teype_vent=fields.Char(string='Type ventilation', required=True)
    type_tva=fields.Char(string='Type TVA')
    impact_tva=fields.Char(string='Impact déclaration TVA')

class ProductTemplate(models.Model):
    _inherit = 'product.template'   
    #teype_vent=fields.Char(string='Ventilation')
    teype_vent = fields.Char(compute='_get_code',string='Ventilation', readonly=True, store=True)
    teype_vent_sale = fields.Char(compute='_get_type_ventsal',string='Ventilation', readonly=True, store=True)
    
    @api.multi
    @api.depends('supplier_taxes_id')
    def _get_code(self):
        data =[]
        if self.supplier_taxes_id:      
            for t in self.supplier_taxes_id:
                data.append(str(t.code_dgi)+'-'+str(t.teype_vent))
            self.teype_vent = (', '.join(map(str, data)))
        else:pass
    
    @api.multi
    @api.depends('taxes_id')
    def _get_type_ventsal(self):
        data =[]
        if self.taxes_id:    
            for t in self.taxes_id:
                data.append(str(t.code_dgi)+'-'+str(t.teype_vent))
            self.teype_vent_sale = (', '.join(map(str, data))) 
        else:pass
            
class ProductProduct(models.Model):
    _inherit = 'product.product'   
    #teype_vent=fields.Char(string='Ventilation')
    teype_vent = fields.Char(compute='_get_code_dgi',string='Ventilation', readonly=True, store=True)
    
    
    
    @api.multi
    @api.depends('supplier_taxes_id')
    def _get_code_dgi(self):  
        data =[]
        for t in self.supplier_taxes_id:
            data.append(str(t.code_dgi)+'-'+str(t.teype_vent))
        self.teype_vent = (', '.join(map(str, data)))
    
        return True 
          


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    
    payment_mode = fields.Many2one('payment.mode',string='Mode de paiement', required=True)
    
    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        """ Match statement lines with existing payments (eg. checks) and/or payables/receivables (eg. invoices and credit notes) and/or new move lines (eg. write-offs).
            If any new journal item needs to be created (via new_aml_dicts or counterpart_aml_dicts), a new journal entry will be created and will contain those
            items, as well as a journal item for the bank statement line.
            Finally, mark the statement line as reconciled by putting the matched moves ids in the column journal_entry_ids.

            :param self: browse collection of records that are supposed to have no accounting entries already linked.
            :param (list of dicts) counterpart_aml_dicts: move lines to create to reconcile with existing payables/receivables.
                The expected keys are :
                - 'name'
                - 'debit'
                - 'credit'
                - 'move_line'
                    # The move line to reconcile (partially if specified debit/credit is lower than move line's credit/debit)

            :param (list of recordsets) payment_aml_rec: recordset move lines representing existing payments (which are already fully reconciled)

            :param (list of dicts) new_aml_dicts: move lines to create. The expected keys are :
                - 'name'
                - 'debit'
                - 'credit'
                - 'account_id'
                - (optional) 'tax_ids'
                - (optional) Other account.move.line fields like analytic_account_id or analytics_id

            :returns: The journal entries with which the transaction was matched. If there was at least an entry in counterpart_aml_dicts or new_aml_dicts, this list contains
                the move created by the reconciliation, containing entries for the statement.line (1), the counterpart move lines (0..*) and the new move lines (0..*).
        """
        counterpart_aml_dicts = counterpart_aml_dicts or []
        payment_aml_rec = payment_aml_rec or self.env['account.move.line']
        new_aml_dicts = new_aml_dicts or []

        aml_obj = self.env['account.move.line']

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        counterpart_moves = self.env['account.move']

        # Check and prepare received data
        if any(rec.statement_id for rec in payment_aml_rec):
            raise UserError(_('A selected move line was already reconciled.'))
        for aml_dict in counterpart_aml_dicts:
            if aml_dict['move_line'].reconciled:
                raise UserError(_('A selected move line was already reconciled.'))
            if isinstance(aml_dict['move_line'], pycompat.integer_types):
                aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])
        for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
            if aml_dict.get('tax_ids') and isinstance(aml_dict['tax_ids'][0], pycompat.integer_types):
                # Transform the value in the format required for One2many and Many2many fields
                aml_dict['tax_ids'] = [(4, id, None) for id in aml_dict['tax_ids']]
        if any(line.journal_entry_ids for line in self):
            raise UserError(_('A selected statement line was already reconciled with an account move.'))

        # Fully reconciled moves are just linked to the bank statement
        total = self.amount
        for aml_rec in payment_aml_rec:
            total -= aml_rec.debit - aml_rec.credit
            aml_rec.with_context(check_move_validity=False).write({'statement_line_id': self.id})
            counterpart_moves = (counterpart_moves | aml_rec.move_id)

        # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
        # case we reconcile the existing and the new move lines together, or being a write-off.
        if counterpart_aml_dicts or new_aml_dicts:
            st_line_currency = self.currency_id or statement_currency
            st_line_currency_rate = self.currency_id and (self.amount_currency / self.amount) or False

            # Create the move
            self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
            move_vals = self._prepare_reconciliation_move(self.statement_id.name)
            move = self.env['account.move'].create(move_vals)
            counterpart_moves = (counterpart_moves | move)

            # Create The payment
            payment = self.env['account.payment']
            if abs(total)>0.00001:
                partner_id = self.partner_id and self.partner_id.id or False
                partner_type = False
                if partner_id:
                    if total < 0:
                        partner_type = 'supplier'
                    else:
                        partner_type = 'customer'

                payment_methods = (total>0) and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                currency = self.journal_id.currency_id or self.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': total >0 and 'inbound' or 'outbound',
                    'partner_id': self.partner_id and self.partner_id.id or False,
                    'partner_type': partner_type,
                    'journal_id': self.statement_id.journal_id.id,
                    'payment_date': self.date,
                    'payment_mode': self.payment_mode and self.payment_mode.id or False,
                    'state': 'reconciled',
                    'currency_id': currency.id,
                    'amount': abs(total),
                    'communication': self._get_communication(payment_methods[0] if payment_methods else False),
                    'name': self.statement_id.name or _("Bank Statement %s") %  self.date,
                })

            # Complete dicts to create both counterpart move lines and write-offs
            to_create = (counterpart_aml_dicts + new_aml_dicts)
            ctx = dict(self._context, date=self.date)
            for aml_dict in to_create:
                aml_dict['move_id'] = move.id
                aml_dict['partner_id'] = self.partner_id.id
                aml_dict['statement_line_id'] = self.id
                if st_line_currency.id != company_currency.id:
                    aml_dict['amount_currency'] = aml_dict['debit'] - aml_dict['credit']
                    aml_dict['currency_id'] = st_line_currency.id
                    if self.currency_id and statement_currency.id == company_currency.id and st_line_currency_rate:
                        # Statement is in company currency but the transaction is in foreign currency
                        aml_dict['debit'] = company_currency.round(aml_dict['debit'] / st_line_currency_rate)
                        aml_dict['credit'] = company_currency.round(aml_dict['credit'] / st_line_currency_rate)
                    elif self.currency_id and st_line_currency_rate:
                        # Statement is in foreign currency and the transaction is in another one
                        aml_dict['debit'] = statement_currency.with_context(ctx).compute(aml_dict['debit'] / st_line_currency_rate, company_currency)
                        aml_dict['credit'] = statement_currency.with_context(ctx).compute(aml_dict['credit'] / st_line_currency_rate, company_currency)
                    else:
                        # Statement is in foreign currency and no extra currency is given for the transaction
                        aml_dict['debit'] = st_line_currency.with_context(ctx).compute(aml_dict['debit'], company_currency)
                        aml_dict['credit'] = st_line_currency.with_context(ctx).compute(aml_dict['credit'], company_currency)
                elif statement_currency.id != company_currency.id:
                    # Statement is in foreign currency but the transaction is in company currency
                    prorata_factor = (aml_dict['debit'] - aml_dict['credit']) / self.amount_currency
                    aml_dict['amount_currency'] = prorata_factor * self.amount
                    aml_dict['currency_id'] = statement_currency.id

            # Create write-offs
            # When we register a payment on an invoice, the write-off line contains the amount
            # currency if all related invoices have the same currency. We apply the same logic in
            # the manual reconciliation.
            counterpart_aml = self.env['account.move.line']
            for aml_dict in counterpart_aml_dicts:
                counterpart_aml |= aml_dict.get('move_line', self.env['account.move.line'])
            new_aml_currency = False
            if counterpart_aml\
                    and len(counterpart_aml.mapped('currency_id')) == 1\
                    and counterpart_aml[0].currency_id\
                    and counterpart_aml[0].currency_id != company_currency:
                new_aml_currency = counterpart_aml[0].currency_id
            for aml_dict in new_aml_dicts:
                aml_dict['payment_id'] = payment and payment.id or False
                if new_aml_currency and not aml_dict.get('currency_id'):
                    aml_dict['currency_id'] = new_aml_currency.id
                    aml_dict['amount_currency'] = company_currency.with_context(ctx).compute(aml_dict['debit'] - aml_dict['credit'], new_aml_currency)
                aml_obj.with_context(check_move_validity=False, apply_taxes=True).create(aml_dict)

            # Create counterpart move lines and reconcile them
            for aml_dict in counterpart_aml_dicts:
                if aml_dict['move_line'].partner_id.id:
                    aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
                aml_dict['account_id'] = aml_dict['move_line'].account_id.id
                aml_dict['payment_id'] = payment and payment.id or False

                counterpart_move_line = aml_dict.pop('move_line')
                if counterpart_move_line.currency_id and counterpart_move_line.currency_id != company_currency and not aml_dict.get('currency_id'):
                    aml_dict['currency_id'] = counterpart_move_line.currency_id.id
                    aml_dict['amount_currency'] = company_currency.with_context(ctx).compute(aml_dict['debit'] - aml_dict['credit'], counterpart_move_line.currency_id)
                new_aml = aml_obj.with_context(check_move_validity=False).create(aml_dict)

                (new_aml | counterpart_move_line).reconcile()

            # Balance the move
            st_line_amount = -sum([x.balance for x in move.line_ids])
            aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
            aml_dict['payment_id'] = payment and payment.id or False
            aml_obj.with_context(check_move_validity=False).create(aml_dict)

            move.post()
            #record the move name on the statement line to be able to retrieve it in case of unreconciliation
            self.write({'move_name': move.name})
            payment and payment.write({'payment_reference': move.name})
        elif self.move_name:
            raise UserError(_('Operation not allowed. Since your statement line already received a number, you cannot reconcile it entirely with existing journal entries otherwise it would make a gap in the numbering. You should book an entry and make a regular revert of it in case you want to cancel it.'))
        counterpart_moves.assert_balanced()
        return counterpart_moves