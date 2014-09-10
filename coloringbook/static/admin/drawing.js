/*
    (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
    Author: Julian Gonggrijp, j.gonggrijp@uu.nl
    
    This script enables the admins to identify colorable areas in a
    newly uploaded SVG image.
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
        enable_confirmation_dialog = function ( ) { };
    }

    // Actual drawing editing logic starts here.
    var current_path,
        former_color,
        panel = $('#area_panel'),
        image = $('#coloring_book_image'),
        hidden_image = $('#svg_source'),
        hidden_list = $('#area_list'),
        form_checkbox = $('#colorable'),
        form_namefield = $('#area_name');
    
    // Unhide and position the #area_panel close to, but preferably not on
    // top of, the SVG path that was clicked. Highlight the path that is
    // being edited. Prefill the form in the #area_panel with known values
    // and best guesses.
    var display_panel = function (event) {
        event.preventDefault();
        if (current_path) cancel_panel(event);
        current_path = $(event.target)
        panel.show().position({
            my: 'left bottom',
            at: 'right top',
            of: current_path,
            within: image
        });
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
    
    // Triggered when the #area_panel form is saved or cancelled.
    var close_panel = function ( ) {
        panel.hide();
        current_path = null;
        former_color = null;
    }
    
    // Triggered when the #cancel_area button is clicked.
    var cancel_panel = function ( ) {
        if (former_color) current_path.attr('fill', former_color);
        close_panel();
    }
    
    // Triggered when the #save_area button is clicked. Validates the
    // #area_name field and updates the hidden input field when
    // applicable.
    var save_panel = function ( ) {
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
            current_path.addClass('colorable');
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
    
    if (image) {
        // Initialize things and attach events to stuff.
        
        image.append(hidden_image.val());
        var svg = $('svg');
        // Below, I can't just use svg.attr(...) directly, because
        // that method converts everything to lowercase.
        if (! svg.get(0).hasAttribute('viewBox')) {
            svg.get(0).setAttribute('viewBox', '0 0 ' + svg.attr('width') + ' ' + svg.attr('height'));
        }
        svg.css('max-height', ($(window).height() - 30) + 'px');
        svg.css('max-width', $('.navbar').width() + 'px');
        $('path').click(display_panel);
        var areas = {};
        if (hidden_list.val()) areas = string2set(hidden_list.val());
        $('#cancel_area').click(cancel_panel);
        $('#save_area').click(save_panel);
        form_namefield.keydown(function (event) {
            switch (event.which) {
            case 13:  // return pressed
                event.preventDefault();
                save_panel();
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
        panel.hide();
        $('.control-label').hide();  // cheap and easy solution
    }
})(window.jQuery);
