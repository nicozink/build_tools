#ifdef _MSC_VER
	#define DISABLE_WARNINGS_BEGIN() __pragma(warning(push));
	#define DISABLE_ALL_WARNINGS_BEGIN() __pragma(warning(push, 0));
	#define DISABLE_WARNINGS_END() __pragma(warning(pop));

	#define DISABLE_WARNING(warn) __pragma(warning( disable : ## warn ## ));
#else
	#define DISABLE_WARNINGS_BEGIN() _Pragma("GCC diagnostic push")
	#define DISABLE_ALL_WARNINGS_BEGIN() _Pragma("message(\"TODO\")")
	#define DISABLE_WARNINGS_END() _Pragma("GCC diagnostic pop")

	#define DISABLE_WARNING(warn) _Pragma("GCC diagnostic ignored \"-W ## warn ## \"")
#endif
