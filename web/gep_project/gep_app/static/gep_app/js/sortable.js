$(document).ready(function() {
	$(".sortable-input").on("change", function() {
		var element = $(this).parent().parent();
		var old_index = $(".sortable-element").index(element);
		var new_index = $(this).val() - 1;
		var max_index = $("#sortable-container").children().length - 1;
		if (new_index < 0 || new_index > max_index) {
			alert("Invalid rank");
			$(this).val(old_index + 1);
			return;
		}
		if(old_index < new_index){
			$(".sortable-element").eq(new_index).after(element);
		} else {
			$(".sortable-element").eq(new_index).before(element);
		}
		$(".sortable-input").each(function(index) {
			$(this).val(index + 1)
		});
	});
})