const plugin = require('tailwindcss/plugin')

module.exports = plugin(function({ addUtilities }) {
  addUtilities({
    '.animation-delay-200': {
      'animation-delay': '200ms',
    },
    '.animation-delay-400': {
      'animation-delay': '400ms',
    },
  })
})
