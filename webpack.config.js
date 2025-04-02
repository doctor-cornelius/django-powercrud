const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

module.exports = {
  entry: {
    htmx: './django_nominopolitan/static/js/htmx-init.js',
    main: [
      './django_nominopolitan/static/js/main.js',
      './django_nominopolitan/static/css/tailwind.css',
    ]
  },
  output: {
    filename: 'js/[name].bundle.js',
    path: path.resolve(__dirname, 'django_nominopolitan/static/dist'),
    publicPath: '../'
  },
  resolve: {
    modules: [
      path.resolve(__dirname, 'node_modules'),
      'node_modules'
    ]
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          format: {
            comments: false,
          },
        },
        extractComments: false,
      }),
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: [
            'default',
            {
              calc: false, // Disable calc optimization
              discardComments: { removeAll: true }
            },
          ],
        },
      }),
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: 'css/bundle.css'
    }),
    new webpack.ProvidePlugin({
      htmx: 'htmx.org',
      bootstrap: 'bootstrap'
    })
  ],
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  'postcss-import',
                  '@tailwindcss/postcss',
                  'autoprefixer'
                ]
              }
            }
          }
        ]
      },
      {
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          'postcss-loader',
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                includePaths: ['node_modules'],
                quietDeps: true
              }
            }
          }
        ]
      }
    ]
  },
  stats: {
    errorDetails: true
  }
};
