var argv         = require('minimist')(process.argv.slice(2));
var autoprefixer = require('gulp-autoprefixer');
var cache        = require('gulp-cached');
var chmod        = require('gulp-chmod');
var concat       = require('gulp-concat');
var git          = require('gulp-git');
var gulp         = require('gulp');
var gulpif       = require('gulp-if');
var pug          = require('gulp-pug');
var livereload   = require('gulp-livereload');
var plumber      = require('gulp-plumber');
var rename       = require('gulp-rename');
var sass         = require('gulp-sass');
var sourcemaps   = require('gulp-sourcemaps');
var uglify       = require('gulp-uglify-es').default;

var enabled = {
    uglify: argv.production,
    maps: !argv.production,
    failCheck: !argv.production,
    prettyPug: !argv.production,
    cachify: !argv.production,
    cleanup: argv.production,
    chmod: argv.production,
};

var destination = {
    css: 'cloud/static/assets/css',
    pug: 'cloud/templates',
    js: 'cloud/static/assets/js',
}

var source = {
    pillar: '../pillar/'
}


/* CSS */
gulp.task('styles', function() {
    gulp.src('src/styles/**/*.sass')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.maps, sourcemaps.init()))
        .pipe(sass({
            outputStyle: 'compressed'}
            ))
        .pipe(autoprefixer("last 3 versions"))
        .pipe(gulpif(enabled.maps, sourcemaps.write(".")))
        .pipe(gulp.dest(destination.css))
        .pipe(gulpif(argv.livereload, livereload()));
});


/* Templates - Pug */
gulp.task('templates', function() {
    gulp.src('src/templates/**/*.pug')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.cachify, cache('templating')))
        .pipe(pug({
            pretty: enabled.prettyPug
        }))
        .pipe(gulp.dest(destination.pug))
        .pipe(gulpif(argv.livereload, livereload()));
    // TODO(venomgfx): please check why 'gulp watch' doesn't pick up on .txt changes.
    gulp.src('src/templates/**/*.txt')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.cachify, cache('templating')))
        .pipe(gulp.dest(destination.pug))
        .pipe(gulpif(argv.livereload, livereload()));
});


/* Tutti gets built by Pillar. See gulpfile.js in pillar.*/


/* Individual Uglified Scripts */
gulp.task('scripts', function() {
    gulp.src('src/scripts/*.js')
        .pipe(gulpif(enabled.failCheck, plumber()))
        .pipe(gulpif(enabled.cachify, cache('scripting')))
        .pipe(gulpif(enabled.maps, sourcemaps.init()))
        .pipe(gulpif(enabled.uglify, uglify()))
        .pipe(rename({suffix: '.min'}))
        .pipe(gulpif(enabled.maps, sourcemaps.write(".")))
        .pipe(gulpif(enabled.chmod, chmod(644)))
        .pipe(gulp.dest(destination.js))
        .pipe(gulpif(argv.livereload, livereload()));
});


// While developing, run 'gulp watch'
gulp.task('watch',function() {
    // Only listen for live reloads if ran with --livereload
    if (argv.livereload){
        livereload.listen();
    }

    gulp.watch('src/styles/**/*.sass',['styles']);
    gulp.watch(source.pillar + 'src/styles/**/*.sass',['styles']);
    gulp.watch('src/scripts/*.js',['scripts']);
    gulp.watch('src/templates/**/*.pug',['templates']);
});


// Erases all generated files in output directories.
gulp.task('cleanup', function() {
    var paths = [];
    for (attr in destination) {
        paths.push(destination[attr]);
    }

    git.clean({ args: '-f -X ' + paths.join(' ') }, function (err) {
        if(err) throw err;
    });

});


// Run 'gulp' to build everything at once
var tasks = [];
if (enabled.cleanup) tasks.push('cleanup');

gulp.task('default', tasks.concat(['styles', 'templates', 'scripts']));
