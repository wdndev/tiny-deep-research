const { sum } = require('./index');

test('hello world!', () => {
	expect(sum(1, 2)).toBe(3);
});