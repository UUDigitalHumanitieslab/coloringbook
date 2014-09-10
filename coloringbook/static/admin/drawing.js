/*
    (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
    Author: Julian Gonggrijp, j.gonggrijp@uu.nl
*/

(function ($) {
    'use strict';
    var display_panel = function (event) {
        event.preventDefault();
        $('#area_panel').show().position({
            my: 'left bottom',
            at: 'right top',
            of: $(event.target),
            collision: 'flip flip'
        });
        $(event.target).attr('fill', 'grey');
    }
    var image = $('#coloring_book_image');
    if (image) {
        image.append($('#svg_source').val());
        var svg = $('svg');
        // Below, I can't just use svg.attr(...) directly, because
        // that method converts everything to lowercase.
        if (! svg.get(0).hasAttribute('viewBox')) {
            svg.get(0).setAttribute('viewBox', '0 0 ' + svg.attr('width') + ' ' + svg.attr('height'));
        }
        svg.css('max-height', ($(window).height() - 30) + 'px');
        svg.css('max-width', $('.navbar').width() + 'px');
        $('path').click(display_panel);
        $('#area_panel').hide();
    }
})(window.jQuery);
