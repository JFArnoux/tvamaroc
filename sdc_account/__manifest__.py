# -*- coding: utf-8 -*-

{
    'name': 'Télédeclaration TVA',
    'version': '1.0',
    'author': 'Ait-Mlouk Addi',
    'website': 'https://www.sdatacave.com',
    'license': "AGPL-3",
    'complexity': 'easy',
    'sequence': 1,
    'category': 'sale',
    'description': """
        Put your description here for your module:
            - model1
            - model2
            - model3
    """,
    'depends': ['base','mail','sale','account'],
    'summary': 'sale, purchase',
    'data': [
        'views/sdc_views.xml',
        'views/sdc_inherit.xml',
        'data/data.xml',
        #'menu.xml',
    ],
    
    'css': [
        #'static/src/css/ModuleName_style.css'
    ],
    
    'installable': True,
    'application': True,
}
