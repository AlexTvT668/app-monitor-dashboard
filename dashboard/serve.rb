#!/usr/bin/env ruby
require 'webrick'
root = File.expand_path(File.dirname(__FILE__))
server = WEBrick::HTTPServer.new(Port: 8765, BindAddress: '127.0.0.1', DocumentRoot: root)
trap('INT'){ server.shutdown }
server.start
