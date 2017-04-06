#!/usr/bin/ruby
require 'date'
require 'cairo'

colors = [:red, :blue, :green, :cyan, :magenta, :yellow]
data = []

if ARGV.count < 1
  puts 'Usage: emailplot.py file1 [file2] [file3] ...'
  exit
end

min_year = DateTime.now.year
max_year = DateTime.now.year + 1

coloridx = 0
ARGV.each { |fn|
  File.open(fn, 'r:ISO-8859-1').each { |line|
    next if not line =~ /^Date: /
    dt = DateTime.parse(line[6..-1])
    x = dt.year*1.0 + ( Date.leap?(dt.year) ? (dt.yday-1)/366.0 : (dt.yday-1)/365.0 )
    min_year = dt.year if dt.year < min_year
    y = (dt.hour*3600.0 + dt.min*60.0 + dt.sec) / 86400.0
    data << [x,y,coloridx]
  }
  coloridx += 1
}

Cairo::ImageSurface.new(640, 480) { |surface|
  cr = Cairo::Context.new(surface)

  cr.set_source_color(:white)
  cr.paint

  cr.move_to(30, 450)
  cr.line_to(620, 450)
  cr.move_to(30, 10)
  cr.line_to(30, 450)
  cr.close_path

  cr.set_source_color(:black)
  cr.set_line_width(1)
  cr.stroke

  (0..4).each { |i|
    cr.move_to(2, 450 - i * 110)
    cr.show_text('%02d:00' % (i * 6))
  }
  (min_year..max_year).each { |i|
    cr.move_to(20.0 + (i - min_year) * 590 / (max_year - min_year), 465)
    cr.show_text(i.to_s)
  }
  cr.stroke

  data.each { |x,y,c|
    cr.set_source_color(colors[c])
    x = 20.0 + (x - min_year) * 590.0 / (max_year - min_year)
    y = 450 - y * 440
    cr.arc(x, y, 1, 0, 2 * Math::PI)
    cr.stroke
  }

  cr.target.write_to_png('emailplot.png')
}
