from django.forms import CheckboxSelectMultiple
from  django.template.loader import get_template

class DropdownMultipleWidget(CheckboxSelectMultiple):
	allow_multiple_selected = True
	input_type = 'checkbox'
	template_name = get_template('dropdown_multiple.html')
	option_template_name = get_template('dropdown_multiple_option.html')