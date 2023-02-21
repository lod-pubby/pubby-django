/*-------------HAMBURGER-MENU-BUTTON------------------*/

$('#sidebarCollapse').click(function(){
   $('#sidebarCollapse > svg').toggleClass('fa-bars fa-xmark')
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

/*-------------------FAB-------------------------*/
$(document).ready(function () {
        $('#fab-button').click(function () {
            $('#issue-sidebar').toggleClass('d-none');
            $(this).toggleClass('d-none');
        });

        $('#fab-cancel').click(function () {
            $('#issue-sidebar').toggleClass('d-none');
            $('#fab-button').toggleClass('d-none');
        });
    });