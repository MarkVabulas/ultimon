import {} from './Client.js';
import {} from './DrawArcGuageDefault.js';
import {} from './DrawGraphDefault.js';

import {} from "./style.css";

const importAll = require =>
    require.keys().reduce((acc, next) => {
      acc[next.replace("./", "")] = require(next);
      return acc;
    }, {});
  
  const images = importAll(
    require.context("./images", false, /\.(png|jpe?g|svg)$/)
  );
  
