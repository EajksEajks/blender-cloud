let argv         = require('minimist')(process.argv.slice(2));
let autoprefixer = require('gulp-autoprefixer');
let cache        = require('gulp-cached');
let chmod        = require('gulp-chmod');
let concat       = require('gulp-concat');
let git          = require('gulp-git');
let gulp         = require('gulp');
let gulpif       = require('gulp-if');
let pug          = require('gulp-pug');
let plumber      = require('gulp-plumber');
let rename       = require('gulp-rename');
let sass         = require('gulp-sass');
let sourcemaps   = require('gulp-sourcemaps');
let uglify       = require('gulp-uglify-es').default;

let enabled = {
    uglify: argv.production,
    maps: !argv.production,
    failCheck: !argv.production,
    prettyPug: !argv.production,
    cachify: !argv.production,
    cleanup: argv.production,
    chmod: argv.production,
};

let destination = {
    css: 'cloud/static/assets/css',
    pug: 'cloud/templates',
    js: 'cloud/static/assets/js',
}

let source = {
    pillar: '../pillar/'
}


/* CSS */
gulp.task('styles', function(done) {
    gulp.src('src/styles/**/*.sass')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.maps, sourcemaps.init()))
        .pipe(sass({
            outputStyle: 'compressed'}
            ))
        .pipe(autoprefixer("last 3 versions"))
        .pipe(gulpif(enabled.maps, sourcemaps.write(".")))
        .pipe(gulp.dest(destination.css));
    done();
});


/* Templates - Pug */
gulp.task('templates', function(done) {
    gulp.src('src/templates/**/*.pug')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.cachify, cache('templating')))
        .pipe(pug({
            pretty: enabled.prettyPug
        }))
        .pipe(gulp.dest(destination.pug));
    // TODO(venomgfx): please check why 'gulp watch' doesn't pick up on .txt changes.
    gulp.src('src/templates/**/*.txt')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.cachify, cache('templating')))
        .pipe(gulp.dest(destination.pug));
    done();
});


/* Tutti gets built by Pillar. See gulpfile.js in pillar.*/


/* Individual Uglified Scripts */
gulp.task('scripts', function(done) {
    gulp.src('src/scripts/*.js')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.cachify, cache('scripting')))
        .pipe(gulpif(enabled.maps, sourcemaps.init()))
        .pipe(gulpif(enabled.uglify, uglify()))
        .pipe(rename({suffix: '.min'}))
        .pipe(gulpif(enabled.maps, sourcemaps.write(".")))
        .pipe(gulpif(enabled.chmod, chmod(0o644)))
        .pipe(gulp.dest(destination.js));
    done();
});


// While developing, run 'gulp watch'
gulp.task('watch',function(done) {
    let watchStyles = [
        'src/styles/**/*.sass',
        source.pillar + 'src/styles/**/*.sass',
    ];

    let watchScripts = [
        'src/scripts/**/*.js',
        source.pillar + 'src/scripts/**/*.js',
    ];

    let watchTemplates = [
        'src/templates/**/*.pug',
        source.pillar + 'src/templates/**/*.pug',
    ];

    gulp.watch(watchStyles, gulp.series('styles'));
    gulp.watch(watchScripts, gulp.series('scripts'));
    gulp.watch(watchTemplates, gulp.series('templates'));
    done();
});


// Erases all generated files in output directories.
gulp.task('cleanup', function(done) {
    let paths = [];
    for (attr in destination) {
        paths.push(destination[attr]);
    }

    git.clean({ args: '-f -X ' + paths.join(' ') }, function (err) {
        if(err) throw err;
    });
    done();
});


// Run 'gulp' to build everything at once
let tasks = [];
if (enabled.cleanup) tasks.push('cleanup');

gulp.task('default', gulp.parallel(tasks.concat(['styles', 'templates', 'scripts'])));
