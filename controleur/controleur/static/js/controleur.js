$(function () {
    function ControleurViewModel(parameters) {
        var self = this;

        self.state = ko.observable(false);

        // Update the ON/OFF button look
        self.updateButton = function() {
    if (self.state()) {
        $("#controleur_power_button")
            .removeClass("btn-success")
            .addClass("btn-danger");
        $("#controleur_power_text").text("Eteindre l'imprimante");
        $("#controleur_emergency_button").css("display", "inline-block"); //set display of Emergency button
    } else {
        $("#controleur_power_button")
            .removeClass("btn-danger")
            .addClass("btn-success");
        $("#controleur_power_text").text("Allumer l'imprimante");
        $("#controleur_emergency_button").css("display", "none");
    }
};

        // Fetch initial state from backend
        self.fetchState = function () {
            OctoPrint.simpleApiCommand("controleur", "get_state", {})
                .done(function (response) {
                    self.state(response.state);
                    self.updateButton();
                })
                .fail(function (err) {
                    console.error("[Controleur] Failed to fetch state:", err);
                });
        };

        // Toggle ON/OFF with backend-driven logic
        self.togglePower = function () {
            OctoPrint.simpleApiCommand("controleur", "toggle", {})
                .done(function (response) {
                    if (response.success) {
                        if (response.disconnect) {
                            // Backend says: disconnect before turning off
                            console.log("[Controleur] Disconnecting printer before power-off...");
                            $("#printer_disconnect").click();

                            setTimeout(function () {
                                OctoPrint.simpleApiCommand("controleur", "finalize_off", {})
                                    .done(function (finalResp) {
                                        self.state(finalResp.state);
                                        self.updateButton();
                                        new PNotify({
                                            title: "Printer Control",
                                            text: finalResp.message,
                                            type: "success",
                                            hide: true,
                                            delay: 3000
                                        });
                                    })
                                    .fail(function () {
                                        new PNotify({
                                            title: "Error",
                                            text: "Failed to finalize power-off",
                                            type: "error",
                                            hide: true,
                                            delay: 4000
                                        });
                                    });
                            }, 1500); // wait for disconnect

                        } else {
                            // Normal toggle without disconnect
                            self.state(response.state);
                            self.updateButton();
                            new PNotify({
                                title: "Printer Control",
                                text: response.message,
                                type: "success",
                                hide: true,
                                delay: 3000
                            });
                        }
                    } else {
                        // Backend returned error
                        new PNotify({
                            title: "Error",
                            text: response.message || "Unknown error",
                            type: "error",
                            hide: true,
                            delay: 4000
                        });
                    }
                })
                .fail(function () {
                    new PNotify({
                        title: "Error",
                        text: "Failed to communicate with backend",
                        type: "error",
                        hide: true,
                        delay: 4000
                    });
                });
        };

        // Bind click to toggle button
        $("#controleur_power_button").click(function () {
            self.togglePower();
        });

        // Emergency power-off button click handler
        $("#controleur_emergency_button").click(function () {
            showConfirmationDialog({
                title: "Emergency Power-Off",
                message: "Are you sure you want to immediately cut power to the printer? This cannot be undone.",
                onproceed: function () {
                    OctoPrint.simpleApiCommand("controleur", "finalize_off", {})
                        .done(function (response) {
                            new PNotify({
                                title: "Emergency Power-Off",
                                text: response.message || "Printer powered off.",
                                type: "success",
                                hide: true,
                                delay: 3000
                            });
                        })
                        .fail(function () {
                            new PNotify({
                                title: "Error",
                                text: "Failed to perform emergency power-off.",
                                type: "error",
                                hide: true,
                                delay: 4000
                            });
                        });
                }
            });
        });

        // Initial button state
        self.fetchState();

        // Keep button state synced every 5s
        setInterval(self.fetchState, 5000);
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: ControleurViewModel,
        dependencies: [],
        elements: ["#navbar_plugin_controleur"]
    });
});

// Auto-connect logic stays separate
$(function() {
    setInterval(function() {
        // Check if already connected by button text
        const connectButton = document.getElementById("printer_connect");
        if (!connectButton) return;

        const buttonText = connectButton.innerHTML.trim().toLowerCase();
        if (buttonText === "disconnect") {
            return; // Already connected
        }

        let targetPort = null;
        $("#connection_ports option").each(function() {
            if ($(this).text().includes("BOSCH Dremel 3D Printer")) {
                targetPort = $(this).val();
                return false; // break loop
            }
        });

        if (!targetPort) {
            console.log("[Controleur] Dremel port not found.");
            return;
        }

        $("#connection_ports").val(targetPort).trigger("change");
        $("#printer_connect").click();

        console.info("[Controleur] Auto-connecting to Dremel on port:", targetPort);
    }, 1000);
});
