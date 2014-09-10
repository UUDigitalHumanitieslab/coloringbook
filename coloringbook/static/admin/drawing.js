/*
    (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
    Author: Julian Gonggrijp, j.gonggrijp@uu.nl
*/

(function ($) {
    'use strict';
    // Some quick tricks to simulate a set datastructure using plain objects
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
    var current_path,
        former_color,
        panel = $('#area_panel'),
        image = $('#coloring_book_image'),
        hidden_image = $('#svg_source'),
        hidden_list = $('#area_list'),
        form_checkbox = $('#colorable'),
        form_namefield = $('#area_name');
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
        form_namefield.focus();
    }
    var close_panel = function ( ) {
        panel.hide();
        current_path = null;
        former_color = null;
    }
    var cancel_panel = function ( ) {
        if (former_color) current_path.attr('fill', former_color);
        close_panel();
    }
    var save_panel = function ( ) {
        var oldname = current_path.attr('id'),
            newname = form_namefield.val();
        if (newname != oldname && newname in areas) {
            alert('This name is already taken by another area.\n' +
                    'Please provide a different name.');
            form_namefield.focus();
            return;
        }
        if (form_checkbox[0].checked) {
            if (! newname) {
                alert('You really have to provide a name.');
                form_namefield.focus();
                return;
            }
            current_path.addClass('colorable');
            current_path.attr('fill', 'white');
        } else {
            current_path.removeClass('colorable');
            current_path.attr('fill', 'black');
        }
        if (oldname) delete areas[oldname];
        areas[newname] = true;
        current_path.attr('id', newname);
        close_panel();
        hidden_list.val(set2string(areas));
        hidden_image.val(image.html());
    }
    if (image) {
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
        var areas = string2set(hidden_list.val());
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
        panel.hide();
        $('.control-label').hide();  // cheap and easy solution
    }
})(window.jQuery);
