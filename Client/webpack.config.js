const webpack = require('webpack');
const pkg = require('./package.json');
const path = require('path');

const HtmlBundlerPlugin = require('html-bundler-webpack-plugin');

const libraryName = 'UltimateSensorMonitor';
const mode = 'production';

module.exports = (env, options) => {
  const libraryTarget = env['output-library-target'];

  return {
    output: {
      clean: true,
      path: path.resolve(__dirname, 'dist'),
      filename: `${libraryName}.min.js`,
      library: libraryName,
      libraryTarget: libraryTarget || 'umd',
      globalObject: '(typeof self !== \'undefined\' ? self : this)', // TODO Hack (for Webpack 4+) to enable create UMD build which can be required by Node without throwing error for window being undefined (https://github.com/webpack/webpack/issues/6522)
      umdNamedDefine: true,
      publicPath: '',
    },
    module: {
      rules: [
        {
          test: /\.css$/i,
          use: ['css-loader'],
        },
        {
          test: /\.(ico|png|svg|jpe?g|gif)$/i,
          type: 'asset/inline',
        },
      ],
    },
    plugins: [
      new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
      }),
      new HtmlBundlerPlugin({
        entry: [
          {
            import: 'src/aida64.html',
            filename: 'aida64.html',
          },
        ],
        js: { inline: true, },
        css: { inline: true, },
        minify: 'auto'
      }),
    ],
    resolve: { 
      alias: { 
        jquery: 'jquery/src/jquery',
        '@images': path.join(__dirname, 'src/images'),
      } 
    },
    performance: false, // disable warning max size (this page could get huge!)
  };
};