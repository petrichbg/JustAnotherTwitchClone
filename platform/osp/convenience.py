import uuid
import os
import markdown
import bleach
import codecs
from random import Random
from datetime import datetime
from django.conf import settings

def format_file_as_uuid( instance, filename, upload_to ):
	ext = filename.split('.')[-1]
	filename = "%s.%s" % ( uuid.uuid4(), ext )
	print( os.path.join( upload_to, filename ) )
	return os.path.join( upload_to, filename )
	
def generate_page_title( title ):
	if len( settings.OSP_SITE_TITLE ) > 0:
		if len( title ) > 0:
			return "{0} - {1}".format( title, settings.OSP_SITE_TITLE )
		else:
			return settings.OSP_SITE_TITLE
	
	return title	
	
def parse_markdown( text ):
	ALLOWED_TAGS = [ 'a', 'em', 'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'p', 'del', 'ins' ]

	output = text
	output = markdown.markdown( output, ['del_ins'] )
	output = output.strip()
	output = bleach.clean( output, tags = ALLOWED_TAGS, strip = True )

	return output
	
# we don't need HTML escaping when corrupting stream name,
# but have to remove <script> tags and things like this
def bleach_span( text ):
	ALLOWED_TAGS = [ 'span' ]
	
	return bleach.clean( text, tags = ALLOWED_TAGS, strip = True )
	
def append_stream_log( log_directory, log_name ):
	date = datetime.now().date()
	year = date.year
	month = date.month
	day = date.day
	
	log_directory = os.path.join( log_directory, "{0}_{1}".format( year, month ) )
	
	try: 
		os.makedirs( log_directory )
	except OSError:
		if not os.path.isdir( log_directory ):
			raise
	
	log_path = os.path.join( log_directory, "{0}_{1}_{2}_{3}.log".format( log_name, year, month, day ) )
	log = codecs.open( log_path, 'a+', 'utf-8' )
	
	return log
	
colors = [ "#000000", "#808080", "#800000", "#ff0000", "#ff00ff", "#008000", "#00ff00", "#ffff00",
"#0000ff", "#00ffff", "#ffa500", "#ee82ee" ]

def corrupt_word_part( word_part, random ):
	underline = ""
	if random.randrange( 0, 2 ) == 0:
		underline = "text-decoration: underline;"
		
	italics = ""
	if random.randrange( 0, 2 ) == 0:
		italics = "font-style: italic"
	
	text_size = ""
	if random.randrange( 0, 2 ) == 0:
		text_size = "font-size: 40px;"
		
	color = ""
	if random.randrange( 0, 2 ) == 0:
		color = "color: " + random.choice( colors )
		
	okay = ""
	if random.randrange( 0, 3 ) == 0:
		okay = "<span style='font-size: 48px'>\U0001f44c</span>"
		
	return "<span style='{0}{1}{2}{3}'>{4}{5}</span>".format( underline, italics, text_size, color, okay, word_part )

def corrupt_word( word, random ):
	if ( len( word ) < 4 ):
		return word
		
	split_point = random.randrange( 0, len( word ) )
	left_part = word[0 : split_point]
	right_part = word[split_point : len( word )]
	
	random_number = random.randrange( 0, 6 )
	if random_number == 0:
		left_part = corrupt_word_part( left_part, random )
	elif random_number == 1:
		right_part = corrupt_word_part( right_part, random )

	return left_part + right_part
	
def corrupt_stream_name( stream_name ):
	random = Random( hash( stream_name ) )

	words = stream_name.split( " " )
	corrupted_stream_name = []
	for word in words:
		if random.randrange( 0, 2 ) == 0:
			word = corrupt_word( word, random )
			
		corrupted_stream_name.append( "<span style='color: {0}'>{1} </span>".format( random.choice( colors ), word ) )
		
	return "".join( corrupted_stream_name )

def symlink_forced( source, destination ):
	try:
		os.symlink( source, destination)
	except OSError as e:
		if os.path.exists( destination ):
			os.remove( destination )
			os.symlink( source, destination )	