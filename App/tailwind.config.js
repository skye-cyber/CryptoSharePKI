/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', /*'[data-mode="dark"]'],*/
  content: ['./templates/*.html',
            './static/js/*.js'],
  theme: {
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
    fontFamily: {
      display: ['Source Serif Pro', 'Georgia', 'serif'],
      body: ['Synonym', 'system-ui', 'sans-serif'],
    },

    extend: {
      colors: {
        'custom-green': '#00ff00',
      },
    },
  },
  plugins: [],
}

