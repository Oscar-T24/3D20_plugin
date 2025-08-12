$(function() {
    function updateButtonState(isOn) {
        const button = $("#printer-toggle-button");
        button.text(isOn ? "Turn Off" : "Turn On");
        button.toggleClass("btn-success", isOn);
        button.toggleClass("btn-danger", !isOn);
    }

    // Initial state
    let printerState = false;

    // Fetch initial state from the backend
    $.ajax({
        url: "/api/plugin/controleur",
        type: "GET",
        success: function(data) {
            printerState = data.is_on;
            updateButtonState(printerState);
        }
    });

    // Handle button click
    $("#printer-toggle-button").click(function() {
        $.ajax({
            url: "/api/plugin/controleur",
            type: "POST",
            data: JSON.stringify({ command: "toggle_printer" }),
            contentType: "application/json",
            success: function(data) {
                printerState = data.is_on;
                updateButtonState(printerState);
            }
        });
    });
});
