$(document).ready(function() {
	function set_elective_data(){
		elective_data = [];
		$('.form-set').each(function(index) {
			slot = $(this).find('#id_form-'+index+'-slot option:selected').val();
			faculty = $(this).find('#id_form-'+index+'-faculty option:selected').val();
			slot_data = {
							'slot':slot,
							'faculty':faculty,
							'max_seats':{}
						}
			$(this).find('.form-set-dept').each(function(){
				dept = $(this).attr('id').replace('id_form-'+index+'-dept','');
				slot_data['max_seats'][dept] = $(this).val();
			})
			elective_data.push(slot_data);
		});
		$('#id_elective_data').val(JSON.stringify(elective_data));
	}
	
	$(document).on('change', '.form-set', set_elective_data);
	$(document).on('click', '.add-slot', set_elective_data);
	$(document).on('click', '.remove-slot', set_elective_data);
	set_elective_data();
})