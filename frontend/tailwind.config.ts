import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class', 'class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
  	extend: {
  		colors: {
  			primary: {
  				'50': '#eff6ff',
  				'100': '#dbeafe',
  				'200': '#bfdbfe',
  				'300': '#93c5fd',
  				'400': '#60a5fa',
  				'500': '#3b82f6',
  				'600': '#2563eb',
  				'700': '#1d4ed8',
  				'800': '#1e40af',
  				'900': '#1e3a8a',
  				'950': '#172554',
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				'50': '#f0fdf4',
  				'100': '#dcfce7',
  				'200': '#bbf7d0',
  				'300': '#86efac',
  				'400': '#4ade80',
  				'500': '#22c55e',
  				'600': '#16a34a',
  				'700': '#15803d',
  				'800': '#166534',
  				'900': '#14532d',
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			dark: {
  				bg: '#0a0a0a',
  				surface: '#1a1a1a',
  				elevated: '#2a2a2a',
  				border: '#333333',
  				hover: '#404040'
  			},
  			cyber: {
  				cyan: {
  					'50': '#ecfeff',
  					'100': '#cffafe',
  					'200': '#a5f3fc',
  					'300': '#67e8f9',
  					'400': '#22d3ee',
  					'500': '#06b6d4',
  					'600': '#0891b2',
  					'700': '#0e7490',
  					'800': '#155e75',
  					'900': '#164e63',
  					DEFAULT: '#06b6d4',
  					glow: '#22d3ee'
  				},
  				blue: {
  					'50': '#eff6ff',
  					'100': '#dbeafe',
  					'200': '#bfdbfe',
  					'300': '#93c5fd',
  					'400': '#60a5fa',
  					'500': '#3b82f6',
  					'600': '#2563eb',
  					'700': '#1d4ed8',
  					'800': '#1e40af',
  					'900': '#1e3a8a',
  					DEFAULT: '#3b82f6',
  					glow: '#60a5fa'
  				},
  				purple: {
  					DEFAULT: '#a855f7',
  					glow: '#c084fc'
  				},
  				green: {
  					DEFAULT: '#10b981',
  					glow: '#34d399'
  				},
  				bg: {
  					dark: '#050a10',
  					surface: '#0a1420',
  					elevated: '#0f1d2e'
  				}
  			},
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		fontFamily: {
  			sans: [
  				'var(--font-inter)',
  				'system-ui',
  				'sans-serif'
  			]
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		keyframes: {
  			'cyber-pulse': {
  				'0%, 100%': {
  					opacity: '1',
  					boxShadow: '0 0 20px rgba(34, 211, 238, 0.5)'
  				},
  				'50%': {
  					opacity: '0.8',
  					boxShadow: '0 0 40px rgba(34, 211, 238, 0.8)'
  				}
  			},
  			'cyber-glow': {
  				'0%, 100%': {
  					textShadow: '0 0 10px rgba(34, 211, 238, 0.8), 0 0 20px rgba(34, 211, 238, 0.6)'
  				},
  				'50%': {
  					textShadow: '0 0 20px rgba(34, 211, 238, 1), 0 0 30px rgba(34, 211, 238, 0.8)'
  				}
  			},
  			'data-flow': {
  				'0%': {
  					transform: 'translateY(0) opacity(0)'
  				},
  				'50%': {
  					opacity: '1'
  				},
  				'100%': {
  					transform: 'translateY(-100%) opacity(0)'
  				}
  			},
  			'number-rise': {
  				'0%': {
  					transform: 'translateY(20px)',
  					opacity: '0'
  				},
  				'100%': {
  					transform: 'translateY(0)',
  					opacity: '1'
  				}
  			},
  			'scan-line': {
  				'0%': {
  					transform: 'translateY(-100%)'
  				},
  				'100%': {
  					transform: 'translateY(100vh)'
  				}
  			},
  			'grid-pulse': {
  				'0%, 100%': {
  					opacity: '0.1'
  				},
  				'50%': {
  					opacity: '0.3'
  				}
  			}
  		},
  		animation: {
  			'cyber-pulse': 'cyber-pulse 2s ease-in-out infinite',
  			'cyber-glow': 'cyber-glow 2s ease-in-out infinite',
  			'data-flow': 'data-flow 3s linear infinite',
  			'number-rise': 'number-rise 0.5s ease-out',
  			'scan-line': 'scan-line 8s linear infinite',
  			'grid-pulse': 'grid-pulse 4s ease-in-out infinite'
  		},
  		boxShadow: {
  			'cyber-sm': '0 0 10px rgba(34, 211, 238, 0.3)',
  			'cyber': '0 0 20px rgba(34, 211, 238, 0.5)',
  			'cyber-lg': '0 0 30px rgba(34, 211, 238, 0.7)',
  			'cyber-blue': '0 0 20px rgba(59, 130, 246, 0.5)',
  			'cyber-purple': '0 0 20px rgba(168, 85, 247, 0.5)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
