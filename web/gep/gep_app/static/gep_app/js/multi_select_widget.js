$(document).ready(function() {
	$('.multi-select-input').each(function() {
		$(this).css('display','none');
		$(this).removeAttr('required'); /* Widget works only for optional select inputs */
		var placeholder = $(this).attr('placeholder')
		var dropdown_list_items = '';
		$(this).children('option').each(function() {
			if ($(this).is(':selected')) { is_checked = 'checked'; } else { is_checked = ''; }
			var value = $(this).attr('value');
			var dropdown_list_item = '<li class="dropdown-list-item">\
								     	<div class="checkbox">\
									       <label><input id="dropdown_list_checkbox_' + value + '" class="dropdown-list-checkbox" ' + is_checked + ' type="checkbox" value="">' + $(this).text() + '</label>\
									    </div>\
								      </li>';
			dropdown_list_items = dropdown_list_items + dropdown_list_item;
		})
		$(this).after('<div class="dropdown multi-select-widget">\
						  <button class="btn dropdown-toggle" type="button" data-toggle="dropdown">' + placeholder + '\
						  <span class="caret"></span></button>\
						  <ul class="dropdown-menu" area-labelledby="dropdown">' + dropdown_list_items + '\
						  </ul>\
					   </div>');
	})

	$('.multi-select-widget input:checkbox').on('click', function() {
		var id = $(this).attr('id');
		var selected_value = id.replace('dropdown_list_checkbox_','');
		var is_selected = $(this).prop('checked');
		$('.multi-select-input option').each(function() {
			if($(this).attr('value') == selected_value) {
				$(this).prop('selected',is_selected);
			}
		})
	})
})