# Independent tally of the eight synthetic rows using the 18 literal source events.
# One column represents the stimulus. A source assignment has even bit parity.
samples = (0..7).flat_map do |number|
  sources = number.to_s(2).rjust(3, '0')
  next [] unless sources.count('1').even?
  [sources + '0', sources + '1']
end
keys = (0..15).map { |number| number.to_s(2).rjust(4, '0') }

nodes = {
  '1' => ->(a, b, c) { a },
  '2' => ->(a, b, c) { b },
  '3' => ->(a, b, c) { c },
  '12' => ->(a, b, c) { a && b },
  '13' => ->(a, b, c) { a && c },
  '23' => ->(a, b, c) { b && c },
  '123' => ->(a, b, c) { a && b && c },
  '1|2' => ->(a, b, c) { a || b },
  '1|3' => ->(a, b, c) { a || c },
  '2|3' => ->(a, b, c) { b || c },
  '1|23' => ->(a, b, c) { a || (b && c) },
  '13|2' => ->(a, b, c) { (a && c) || b },
  '12|3' => ->(a, b, c) { (a && b) || c },
  '12|13' => ->(a, b, c) { (a && b) || (a && c) },
  '12|23' => ->(a, b, c) { (a && b) || (b && c) },
  '13|23' => ->(a, b, c) { (a && c) || (b && c) },
  '1|2|3' => ->(a, b, c) { a || b || c },
  '12|13|23' => ->(a, b, c) { (a && b) || (a && c) || (b && c) }
}
orders = %w[123 132 213 231 312 321]
lines = []
orders.each do |order|
  positions = order.each_char.map { |digit| digit.to_i - 1 }
  by_position = ->(row) { positions.map { |old| row[old] }.join + row[-1] }
  rows = samples.map(&by_position)
  keys.each do |original_key|
    key = by_position.call(original_key)
    nodes.each_key do |name|
      mapped = name.split('|').map do |branch|
        branch.each_char.map { |digit| (order.index(digit) + 1).to_s }.sort.join
      end.sort.join('|')
      predicate = nodes.fetch(mapped)
      u = v = t = 0
      rows.each do |row|
        same_target = row[-1] == key[-1]
        t += 1 if same_target
        next unless predicate.call(row[0] == key[0], row[1] == key[1], row[2] == key[2])
        u += 1
        v += 1 if same_target
      end
      lines << [order, original_key, name, key, mapped, rows.size, u, v, t].join("\t")
    end
  end
end
puts lines.sort
