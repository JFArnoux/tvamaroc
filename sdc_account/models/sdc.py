from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons import decimal_precision as dp

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
    idfp = fields.Char(string='Identifiant tax professionnelle')
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
    city_id = fields.Char(string='Ville du diège')
    
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
    code=fields.Char(string='Code DGI', required=True)
    partner_def=fields.Boolean(string='Par défaut encaissements clients')
    supplier_def=fields.Boolean(string='Par défaut règlements fournisseurs')
    expense_def=fields.Boolean(string='Par défaut remboursement notes de frais')
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
    teype_vent = fields.Char(string='Ventilation', related='taxes_id.teype_vent', readonly=True)
    
    
        
    
            
