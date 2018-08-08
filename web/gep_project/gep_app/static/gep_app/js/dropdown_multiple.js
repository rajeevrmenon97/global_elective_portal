/* Changes the dropdown content with respect to the checked items in the dropdown menu */
$(document).ready(function() {
	var DEFAULT_DROPDOWN_CONTENT = 'No slots chosen';
	var DROPDOWN_CHECKBOXES = '.dropdown .dropdown-item .form-check-input';
	var DROPDOWN_TOGGLE = '.dropdown #dropdown-btn';
	var DROPDOWN_INPUT = '.dropdown .dropdown-content';
	$(DROPDOWN_CHECKBOXES).on('change load', function() {
		var dropdownContent = '';
		var inputContent = '';
		$(DROPDOWN_CHECKBOXES).each(function() {
			if($(this).prop('checked')) {
				dropdownContent = $(this).next().text() + ', ' + dropdownContent;
				inputContent = $(this).val() + ',' + inputContent;
			}
		});
		dropdownContent = (dropdownContent == '') ? DEFAULT_DROPDOWN_CONTENT : dropdownContent.slice(0,-2);
		inputContent = (inputContent == '') ? inputContent : inputContent.slice(0,-1);
		$(DROPDOWN_TOGGLE).text(dropdownContent);
		$(DROPDOWN_INPUT).first().val(inputContent);
	});
});
