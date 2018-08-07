/* Changes the dropdown content with respect to the checked items in the dropdown menu */
$(document).ready(function() {
	var DEFAULT_DROPDOWN_CONTENT = 'No slots chosen';
	var DROPDOWN_CHECKBOXES = '.dropdown .dropdown-item .form-check-input';
	var DROPDOWN_TOGGLE = '.dropdown #dropdown-btn';
	var DROPDOWN_CONTENT = '.dropdown #dropdown-content';
	$(DROPDOWN_CHECKBOXES).on('change', function() {
		var dropdownContent = '';
		$(DROPDOWN_CHECKBOXES).each(function() {
			if($(this).prop('checked')) {
				dropdownContent = $(this).next().text() + ', ' + dropdownContent;
			}
		});
		dropdownContent = (dropdownContent == '') ? DEFAULT_DROPDOWN_CONTENT : dropdownContent.slice(0,-2);
		$(DROPDOWN_TOGGLE).text(dropdownContent);
	});
	$(DROPDOWN_TOGGLE).bind('DOMSubtreeModified', function() {
		$(DROPDOWN_CONTENT).val($(DROPDOWN_TOGGLE).text());
	});
});
