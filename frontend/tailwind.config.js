/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Sora", "system-ui", "sans-serif"],
      },
      colors: {
        foam: {
          50: "#faf6f1",
          100: "#f2ebe2",
          200: "#e6d9cb",
          300: "#d2bda7",
          400: "#b99a7a",
          500: "#a07f5f",
          600: "#86664b",
          700: "#6c5140",
          800: "#5a4437",
          900: "#4b3a31",
          950: "#28201b",
        },
        roast: {
          50: "#f7f2ec",
          100: "#ebe2d7",
          200: "#d8c6b3",
          300: "#c0a48a",
          400: "#a88466",
          500: "#926d50",
          600: "#7b5742",
          700: "#644636",
          800: "#543b30",
          900: "#48332a",
          950: "#271b16",
        },
        cocoa: {
          50: "#f8f3ee",
          100: "#eee2d4",
          200: "#dbc3a8",
          300: "#c5a07a",
          400: "#b28257",
          500: "#9e6b42",
          600: "#875537",
          700: "#6d442e",
          800: "#5b3a2a",
          900: "#4d3225",
          950: "#2a1a13",
        },
      },
    },
  },
  plugins: [],
};
