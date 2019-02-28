function follow( username ) { 
    //it seems dumb to rely on button's class
    var isFollowing = $( "#followButton" ).hasClass( "btn-danger" );
    if ( isFollowing ) {
        $.ajax({
            url : '/service/unfollow/' + username + '/',
            type : "POST",
            success: function() {
                $( "#followButton" ).removeClass( "btn-danger" );
                $( "#followButton" ).addClass( "btn-primary" );
                $( "#followButtonGlyph" ).removeClass( "glyphicon-heart-empty" );
                $( "#followButtonGlyph" ).addClass( "glyphicon-heart" );
                $( "#followButtonLabel" ).text( "Подписаться" );
            }
        });
    } else {
        $.ajax({
            url : '/service/follow/' + username + '/',
            type : "POST",
            success: function() {
                $( "#followButton" ).removeClass( "btn-primary" );
                $( "#followButton" ).addClass( "btn-danger" );
                $( "#followButtonGlyph" ).removeClass( "glyphicon-heart" );
                $( "#followButtonGlyph" ).addClass( "glyphicon-heart-empty" );
                $( "#followButtonLabel" ).text( "Отписаться" );

            }
        });
    }
}