// Booking form AJAX handling
$(document).ready(function() {
    $('#booking-form').on('submit', function(e) {
        e.preventDefault();
        
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    // Show success message
                    $('#booking-message').html('<div class="alert alert-success">Booking created successfully!</div>');
                    // Redirect after 2 seconds
                    setTimeout(function() {
                        window.location.href = response.redirect_url;
                    }, 2000);
                } else {
                    // Show form errors
                    $('#booking-message').html('<div class="alert alert-danger">' + response.errors + '</div>');
                }
            },
            error: function(xhr, errmsg, err) {
                $('#booking-message').html('<div class="alert alert-danger">An error occurred. Please try again.</div>');
            }
        });
    });
}); 