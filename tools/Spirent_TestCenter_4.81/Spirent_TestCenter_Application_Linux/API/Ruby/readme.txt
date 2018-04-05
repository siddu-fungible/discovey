Set up Ruby

Please consult the Spirent TestCenter Base and Test Package Release Notes for supported versions of Ruby. Release notes are included on the DVD and are available as a “Related Resource” on each software download page (http://support.spirent.com).

To verify that a supported version of Ruby is installed:

1  Open a terminal window.
2  Type ruby -v.

To set up Ruby to run with Spirent TestCenter:

1  Open spirenttestcenter.rb and replace the STC_INSTALL_DIR string with the absolute Spirent TestCenter Application installation path. 
Use forward slashes (/). Start and end the path with an apostrophe('). For example:
	Before replace:
	ENV['STC_PRIVATE_INSTALL_DIR'] = STC_INSTALL_DIR
	After replace:
	ENV['STC_PRIVATE_INSTALL_DIR'] = 'C:/Program Files/Spirent Communications/Spirent TestCenter 3.00/Spirent TestCenter Application/'

2  Confirm that Ruby gem is in your path, and then build the spirenttestcenter gem by running this statement from the command line:
gem build spirenttestcenter.gemspec

3  Install the generated gem file by running this from the command line:
gem install spirenttestcenter-X.X.X.gem
Replace x’s with the correct Spirent TestCenter version.

4  Confirm that your Ruby set up is correct by running the following from the command line:
	irb
	require 'rubygems'
	require 'spirenttestcenter'
	Stc.get('system1', 'version')

Ruby returns the Spirent TestCenter version.

Ruby is ready to be used with Spirent TestCenter.