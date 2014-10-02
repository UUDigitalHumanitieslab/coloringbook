/*
    (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
    Author: Julian Gonggrijp, j.gonggrijp@uu.nl
    
    This script enables the admins to identify colorable areas in a
    newly uploaded SVG image, as well as to express expectations for a
    particular page in which the SVG image is used.
*/

(function ($) {
    'use strict';

    // Some quick tricks to simulate a set datastructure using plain objects.
    function string2set (str) {
        var set_emulation = {};
        var substrings = str.split(',');
        for (var l = substrings.length, i = 0; i < l; ++i) {
            set_emulation[substrings[i]] = true;
        }
        return set_emulation;
    }
    function set2string (set) {
        return Object.keys(set).join(',');
    }

    // Set-once page unload confirmation dialog.
    function enable_confirmation_dialog ( ) {
        $(window).on('beforeunload', function (e) {
            return ('You have unsaved changes, are you sure ' +
                    'you want to leave the page?');
        });
        $('form').submit(function (e) { $(window).off('beforeunload'); });
        enable_confirmation_dialog = function ( ) { };
    }

    // Actual drawing editing logic starts here.
    var current_path,
        former_color,
        panel = $('#area_panel'),
        image = $('#coloring_book_image'),
        hidden_image = $('#svg_source'),
        hidden_list = $('#area_list'),
        hidden_fname = $('#fname'),
        hidden_table = $('#expect_list'),
        form_radio = $('input[type="radio"][name="where"]'),
        form_checkbox = $('#colorable'),
        form_namefield = $('#area_name');
    
    function display_panel (prefill_func) {
        // Unhide and position the #area_panel close to, but preferably not on
        // top of, the SVG path that was clicked. Highlight the path that is
        // being edited. Prefill the form in the #area_panel with known values
        // and best guesses.
        return function (event) {
            event.preventDefault();
            if (current_path) cancel_panel(event);
            current_path = $(event.target)
            panel.show().position({
                my: 'left bottom',
                at: 'right top',
                of: current_path,
                within: image
            });
            prefill_func();
        }
    }
    
    // Used as the prefill_func above for area editing.
    function prefill_area ( ) {
        var css = current_path.css('fill'),
            fill = current_path.attr('fill'),
            id = current_path.attr('id');
        if (css) {
            former_color = css;
            current_path.css('fill', '');
        } else if (fill) {
            former_color = fill;
        }
        current_path.attr('fill', 'grey');
        if (id) $('#area_name').val(id);
        if (!current_path.hasClass('colorable') && former_color == '#000000') {
            form_checkbox.prop('checked', false);
        } else {
            form_checkbox.prop('checked', true);
        }
        form_checkbox.change();
    }
    
    // Used as the prefill_func above for expectation editing.
    function prefill_expectation ( ) {
        var id = current_path.attr('id');
        form_namefield.text(id);
        if (id in expectations) {
            $(expectations[id].color).click();
            if (expectations[id].here) {
                form_radio[0].click();
            } else {
                form_radio[1].click();
            }
        } else {
            form_radio[0].click();
        }
    }
    
    // Triggered when the #area_panel form is saved or cancelled.
    function close_panel ( ) {
        panel.hide();
        current_path = null;
        former_color = null;
    }
    
    // Triggered when the #cancel_area button is clicked.
    function cancel_panel ( ) {
        if (former_color) current_path.attr('fill', former_color);
        close_panel();
    }
    
    // Triggered when the #save_area button is clicked (for areas).
    // Validates the #area_name field and updates the hidden input
    // field when applicable.
    function save_area ( ) {
        var oldname = current_path.attr('id'),
            newname = form_namefield.val();
        if (form_checkbox[0].checked) {
            if (! newname) {
                alert('You really have to provide a name.');
                form_namefield.focus();
                return;
            }
            if (newname != oldname && newname in areas) {
                alert('This name is already taken by another area.\n' +
                        'Please provide a different name.');
                form_namefield.focus();
                return;
            }
            if (current_path.attr('class')) {
                current_path.addClass('colorable');
            } else {
                current_path.attr('class', 'colorable');
            }
            current_path.attr('fill', 'white');
            current_path.attr('id', newname);
            if (oldname) delete areas[oldname];
            areas[newname] = true;
        } else {
            current_path.removeClass('colorable');
            current_path.attr('fill', 'black');
            if (oldname) delete areas[oldname];
        }
        close_panel();
        hidden_list.val(set2string(areas));
        hidden_image.val(image.html());
        enable_confirmation_dialog();
    }
    
    // Triggered when the #save_area button is clicked (for
    // expectations). Processes the form input and updates the hidden
    // field.
    function save_expectation ( ) {
        var id = current_path.attr('id'),
            color = color_chosen.data('color'),
            here = (form_radio.filter(':checked').val() === 'true');
        render_expectation(current_path, color, here);
        expectations[id] = {'color': color, 'here': here};
        close_panel();
        hidden_table.val(JSON.stringify(expectations));
        enable_confirmation_dialog();
    }
    
    // Triggered when the #remove_expectation button is clicked.
    function remove_expectation ( ) {
        var id = current_path.attr('id');
        render_expectation(current_path);
        delete expectations[id];
        close_panel();
        hidden_table.val(JSON.stringify(expectations));
        enable_confirmation_dialog();
    }
    
    // Visually display the expectation for a given $(path): solid
    // fill if the given color is expected in the given path, slightly
    // translucent fill if the color is expected elsewhere.
    function render_expectation (path, color, here) {
        if (! color) {
            // This might be risky.
            path.attr({'fill': 'white', 'fill-opacity': 1});
        } else if (here) {
            path.attr({'fill': color, 'fill-opacity': 1});
        } else {
            path.attr({'fill': color, 'fill-opacity': 0.5});
        }    
    }
    
    // Place the SVG in the page and ensure that it is scaled properly.
    function place_svg (data) {
        image.append(data);
        var svg = $('svg');
        // Below, I can't just use svg.attr(...) directly, because
        // that method converts everything to lowercase.
        if (! svg.get(0).hasAttribute('viewBox')) {
            svg.get(0).setAttribute('viewBox', '0 0 ' + svg.attr('width') + ' ' + svg.attr('height'));
        }
        svg.css('max-height', ($(window).height() - 30) + 'px');
        svg.css('max-width', $('.navbar').width() + 'px');
    }
    
    if (image) {
        // Initialize things and attach events to stuff.
        
        if (hidden_list.length) {
            place_svg(hidden_image.val());
            $('path').click(display_panel(prefill_area));
            var areas = {};
            if (hidden_list.val()) areas = string2set(hidden_list.val());
            $('#save_area').click(save_area);
            form_namefield.keydown(function (event) {
                switch (event.which) {
                case 13:  // return pressed
                    event.preventDefault();
                    save_area();
                    break;
                case 27:  // escape pressed
                    event.preventDefault();
                    cancel_panel();
                }
            });
            form_checkbox.change(function (event) {
                if (event.target.checked) {
                    form_namefield.prop('disabled', false).focus();
                } else {
                    form_namefield.prop('disabled', true);
                }
            });
        } else if (hidden_table.length) {
            var expectations = JSON.parse(hidden_table.val());
            var url = '/static/' + hidden_fname.val() + '.svg';
            $.get(url, null, function (svg) {
                place_svg(svg);
                $('path[class~="colorable"]').click(
                    display_panel(prefill_expectation)
                );
                for (var id in expectations) {
                    render_expectation(
                        $('#' + id),
                        expectations[id].color,
                        expectations[id].here
                    );
                }
            }, 'html');
            insert_swatches(colors);
            $('#save_area').click(save_expectation);
            $('#remove_expectation').click(remove_expectation);
        }
        $('#cancel_area').click(cancel_panel);
        panel.draggable().hide();
    }
})(window.jQuery);
