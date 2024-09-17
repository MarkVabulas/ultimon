const webpack = require('webpack');
const pkg = require('./package.json');
const path = require('path');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlInlineScriptPlugin = require('html-inline-script-webpack-plugin');
const HtmlBundlerPlugin = require('html-bundler-webpack-plugin');

const libraryName = 'UltimateSensorMonitor';
const mode = 'production';

const build_plugins = [
  new webpack.ProvidePlugin({
    $: 'jquery',
    jQuery: 'jquery',
  }),
  new HtmlWebpackPlugin({
    template: 'src/index.html',
    filename: 'index-build.html',
    inject: 'body',
  }),
  new HtmlInlineScriptPlugin(),
];

module.exports = (env, options) => {
  const libraryTarget = env['output-library-target'];
  const stage = options['env']['stage'];

  if (stage == "compile") {
    return {
      entry: `${__dirname}/index.js`,
      output: {
        clean: true,
        path: path.resolve(__dirname, 'build'),
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
            use: ['style-loader', 'css-loader'],
          },
          {
            test: /\.(png|svg|jpg|jpeg|gif)$/i,
            type: 'asset/resource',
            generator: {
             // keep original filenames and copy images to `dist/img/`
             filename: '[name][ext]', 
            },
          },
        ],
      },
      plugins: build_plugins,
      resolve: { alias: { jquery: "jquery/src/jquery" } }
    };
  } else if (stage == "bundle") {
    return {
      output: { clean: true, },
      plugins: [
        new HtmlBundlerPlugin({
          entry: [
            {
              import: 'build/index-build.html',
              filename: 'index.html',
            },
          ],
          js: { inline: true, },
          css: { inline: true, },
        }),
      ],
      module: {
        rules: [
          {
            test: /\.(css|sass|scss)$/,
            use: ['css-loader', 'sass-loader'],
          },
          // inline all assets: images, svg, fonts
          {
            test: /\.(png|jpe?g|webp|svg|woff2?)$/i,
            type: 'asset/inline',
          },
        ],
      },
      performance: false, // disable warning max size
    };
  }
};
