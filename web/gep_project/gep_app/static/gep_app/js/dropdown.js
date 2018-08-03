/* Changes the dropdown content with respect to the checked items in the dropdown menu */
$(document).ready(function() {
	  $(document).on('change', '.dropdown .dropdown-item .form-check-input', function() {
		  var DEFAULT_DROPDOWN_CONTENT = 'Choose Slots';
		  var dropdownContent = '';
		  $('.dropdown .dropdown-item .form-check-input').each(function() {
			  if($(this).prop('checked')) {
				  dropdownContent = $(this).next().text() + ', ' + dropdownContent;
			  }
		  });
		  dropdownContent = (dropdownContent == '') ? DEFAULT_DROPDOWN_CONTENT : dropdownContent.slice(0,-2);
		  $('.dropdown .dropdown-toggle').first().text(dropdownContent);
	  })
});
