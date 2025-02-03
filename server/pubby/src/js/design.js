/*-------------HAMBURGER-MENU-BUTTON------------------*/

$('#sidebarCollapse').click(function(){
   $('#sidebarCollapse > svg').toggleClass('fa-bars fa-xmark')
});

/*-------------------SIDEBAR-------------------------*/
$(document).ready(function () {
            $("#sidebar").mCustomScrollbar({
                theme: "minimal"
            });

            $('#sidebarCollapse').on('click', function () {
                $('#sidebar, #content').toggleClass('active');
                $('.collapse.in').toggleClass('in');
                $('a[aria-expanded=true]').attr('aria-expanded', 'false');
            });
        });

/*------------Sidebar active page highlighting---------------*/

$(document).ready(function ($) {
    var path = window.location.pathname.split("/").pop();

    if( path == ''){
        path = ''; /*das ist die Startseite von Labs http://labs.judaicalink.org/!leer!/*/
    }

    var target = $('#sidebar a[href="'+path+'"]');

    target.addClass('active');
    });

/*---------------------------------------------------*/