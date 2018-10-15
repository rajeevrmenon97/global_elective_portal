$(document).ready(function() {
	$('.single-select-input').each(function() {
		$(this).css('display','none');
		$(this).removeAttr('required'); /* Widget works only for optional select inputs */
		var content = $(this).attr('placeholder');
		var dropdown_list_items = '';
		$(this).children('option').each(function() {
			if ($(this).is(':selected')) { content = $(this).text(); }
			var value = $(this).attr('value');
			var dropdown_list_item = '<li class="dropdown-list-item">\
									     <label><input type="hidden" value="' + value + '">' + $(this).text() + '</label>\
								      </li>'
			dropdown_list_items = dropdown_list_items + dropdown_list_item;
		})
		$(this).after('<div class="dropdown single-select-widget">\
						  <button class="btn dropdown-toggle" type="button" data-toggle="dropdown">' + content + '</button>\
						  <ul class="dropdown-menu" area-labelledby="dropdown">' + dropdown_list_items + '</ul>\
					   </div>');
	})

	$('.single-select-widget .dropdown-list-item').on('click', function() {
		var widget = $(this).closest('.single-select-widget');
		var widget_button = widget.children('.dropdown-toggle:first');
		var selected_input = $(this).find('input:first');
		var selected_value = selected_input.val();

		$('.single-select-input option').each(function() {
			if($(this).attr('value') == selected_value) {
				$(this).prop('selected','selected');
				content = $(this).text();
				widget_button.text(content)
			}
		})
	})
})