$(document).ready(function() {
	function updateElementOnAddition(element, total) {
		if (element.attr('id')) {
			var attr = element.attr('id').replace('-' + (total-1) + '-', '-' + total + '-');
			element.attr({'id': attr});
		}
		if (element.attr('for')) {
			var attr = element.attr('for').replace('-' + (total-1) + '-', '-' + total + '-');
			element.attr({'for': attr});
		}
	}
	
	function updateElementOnRemoval(element, index) {
		if (element.attr('id')) {
			var attr = element.attr('id').replace(/-\d-/g, '-' + index + '-');
			element.attr('id', attr);
		}
		if (element.attr('for')) {
			var attr = element.attr('for').replace(/-\d-/g, '-' + index + '-');
			element.attr('for', attr);
		}
	}
	
	function cloneMore(selector) {
		var newElement = $(selector+":last").clone(true);
		var total = $(selector).length;
		newElement.find('input, select, label').each(function() {
			updateElementOnAddition($(this),total)
		});
		updateElementOnAddition(newElement, total)
		$(selector+":last").find('.add-slot').each(function() {
			var class_name = $(this).attr('class').replace('add-slot', 'remove-slot');
			$(this).attr({'class': class_name});
			$(this).val('-')
		});
		$(selector+":last").after(newElement);
	}
	
	function deleteForm(btn, selector) {
		total = $(selector).length;
		if(total > 1) {
			btn.closest(selector).remove();
			for(var i=0; i<total; i++) {
				$($(selector).get(i)).find('input, select, label').each(function() {
					updateElementOnRemoval($(this),i);
				});
			}
		}
	}
	
	$(document).on('click', '.add-slot', function(e){
		e.preventDefault();
		cloneMore('.form-set');
	});
	
	$(document).on('click', '.remove-slot', function(e){
		e.preventDefault();
		deleteForm($(this), '.form-set');
	});
})